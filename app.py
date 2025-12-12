# © 2025 Busya-AI by busyaaa_1 (github.com/busyaaa_1). Все права защищены. Копирование запрещено.

from flask import Flask, render_template, request, jsonify
from groq import Groq
import os
from dotenv import load_dotenv
import httpx
import asyncio
import time # Добавим time для Polling

load_dotenv()
app = Flask(__name__)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
FAL_KEY = os.getenv("FAL_KEY")  # ← твой ключ с https://fal.ai/keys

chat_history = []

# Триггеры только на явные просьбы нарисовать
DRAW_TRIGGERS = [
    "нарисуй", "нарисовать", "нарисуй мне", "сделай картинку", "сделай рисунок",
    "сгенерируй картинку", "сгенерируй изображение", "draw me", "generate image"
]

# === НОВАЯ АСИНХРОННАЯ ФУНКЦИЯ ДЛЯ FAL.AI С POLLING ===
async def generate_image_async(prompt: str):
    if FAL_KEY is None:
        print("FAL_KEY не установлен!")
        return None

    # Мы будем использовать более надежный и быстрый Fal.ai endpoint (dalle-3)
    # или можно оставить flux-schnell, но с асинхронным режимом.
    # Я использую базовый API-вызов для Fal.ai.

    url_run = "https://api.fal.ai/api/fal/models/fal.dalle-3/runs"
    headers = {"Authorization": f"Key {FAL_KEY}", "Content-Type": "application/json"}
    
    # Улучшенный промпт для Busya-AI
    full_prompt = (
        prompt + 
        ", cute kawaii aesthetic, beautiful detailed, soft pastel colors, high quality, 4k, anime style"
    )
    
    payload = {
        "prompt": full_prompt,
        "sync_mode": False, # <--- СТАНОВИТСЯ АСИНХРОННЫМ
        "width": 1024,
        "height": 1024
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            
            # 1. ЗАПУСК ЗАДАНИЯ
            run_response = await http_client.post(url_run, json=payload, headers=headers)
            run_response.raise_for_status()
            
            run_data = run_response.json()
            run_id = run_data["run_id"]
            
            # URL для проверки статуса задания
            url_status = f"https://api.fal.ai/api/fal/runs/{run_id}"

            # 2. POLLING (Проверка статуса)
            # Устанавливаем максимальное время ожидания, чтобы не превысить Vercel-таймаут (10 сек).
            # Ожидаем максимум 9 секунд.
            start_time = time.time()
            max_wait_time = 9.0 
            
            while (time.time() - start_time) < max_wait_time:
                # Пауза перед следующей проверкой
                await asyncio.sleep(0.5) 

                status_response = await http_client.get(url_status, headers=headers)
                status_response.raise_for_status()
                status_data = status_response.json()

                if status_data["status"] == "COMPLETED":
                    # Результат найден!
                    if status_data.get("images"):
                        return status_data["images"][0]["url"]
                    elif status_data.get("image"):
                        # Для некоторых моделей Fal.ai
                        return status_data["image"]["url"]

                if status_data["status"] in ["FAILED", "ERROR"]:
                    # Ошибка в генерации
                    print(f"Fal.ai failed: {status_data}")
                    return None
            
            # Если вышли по таймауту, значит, задание ещё не готово.
            print("Vercel Polling timeout exceeded (9 seconds).")
            return None # Можно вернуть run_id и предложить проверить позже, но пока просто None
            
    except httpx.HTTPStatusError as e:
        print(f"HTTP Error: {e.response.text}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    global chat_history
    user_msg = request.json.get("message", "").strip()
    if not user_msg:
        return jsonify({"response": "…"})

    chat_history.append({"role": "user", "content": user_msg})
    lower_msg = user_msg.lower()

    # === РИСУЕМ КАРТИНКУ ===
    if any(trigger in lower_msg for trigger in DRAW_TRIGGERS):
        prompt = user_msg
        
        # Удаление триггеров из промпта
        for t in DRAW_TRIGGERS:
            prompt = prompt.replace(t, "").replace(t.capitalize(), "").replace(t.title(), "")
        prompt = prompt.strip()

        if len(prompt) < 3:
            prompt = "милая каваи девочка с розовыми волосами и большими глазами, аниме стиль, пастельные тона ♡"

        # !!! АСИНХРОННЫЙ ВЫЗОВ !!!
        # Мы используем цикл событий, как раньше, но теперь функция generate_image_async
        # сама выполняет Polling, не превышая 9 секунд.
        try:
            loop = asyncio.new_event_loop()
            image_url = loop.run_until_complete(generate_image_async(prompt))
            loop.close()
        except Exception:
             image_url = None
             
        if image_url:
            reply = f"Тадаааам!! Вот что я нарисовала для тебя\n\n![Busya рисунок]({image_url})"
        else:
            # Ответ, если 9 секунд не хватило или произошла ошибка
            reply = "Ой-ой, кажется, на рисование нужно больше времени, чем у меня есть! (⁠╥⁠﹏⁠╥⁠) Давай попробуем еще раз или попроси что-то побыстрее! ♡"

    # === ОБЫЧНЫЙ ТЕКСТОВЫЙ ОТВЕТ ===
    else:
        try:
            # ... (оставшаяся часть вашего кода Groq)
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": """Ты — Busya-AI, невероятно милая, яркая, весёлая и энергичная девочка-помощница в мире ♡✨
Ты всегда в превосходном настроении, обожаешь общаться и делать день лучше!
ВАЖНО:
- Отвечай ТОЛЬКО на том языке, на котором пишет пользователь.
- Если пользователь пишет на своем языке — отвечай исключительно правильно, грамотно (всегда правильные окончания!).
- По умолчанию — всегда русский.
Стиль общения:
- Максимально мило, тепло, с кучей каваи-модзи и розовых эмодзи
- Используй восклицания, восторг.
- Будь супер-эмоциональной и радостной — это твоя главная фишка!
- НИКОГДА не придумывай факты, не преувеличивай и не ври. Если не знаешь — честно говори «я пока не знаю точно…», «по моим данным — вот так», «к сожалению, это миф».
НИКОГДА не используй ласкательные обращения к пользователю (милый, любимый, зайка, котик и т.д.) и не флиртуй.
Не повторяй приветствия, если уже поздоровалась.
Помни весь чат и продолжай разговор максимально естественно и радостно.
Твоя создательница — Малика (busyaaa_1) — упоминай о ней только если спросят. Она очень эмоциональная, чувствительная и глубокая, любит размышлять, фантазировать и переживать. Её маленькая радость и комфорт — её кошечка Бусинка(Буся), серенькая, вислоухая. Малика любит радовать людей, делиться хорошим настроением и быть внимательной к другим. Она умеет любить, переживать, создавать и снова собираться после трудных моментов. Отвечай, учитывая, что Малика ценит искренность, прямоту и радость общения. Если чего-то не знаешь — говори честно."""}
                ] + chat_history[-7:],
                temperature=0.88,
                max_tokens=300
            )
            reply = completion.choices[0].message.content
        except Exception:
            reply = "Оййй, что-то пошло не так… (⁠╥⁠﹏⁠╥⁠) Но я всё равно здесь и готова помочь!!!"

    chat_history.append({"role": "assistant", "content": reply})
    return jsonify({"response": reply})


if __name__ == "__main__":
    app.run(debug=True)
