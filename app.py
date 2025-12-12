# © 2025 Busya-AI by busyaaa_1 (github.com/busyaaa_1). Все права защищены. Копирование запрещено.

from flask import Flask, render_template, request, jsonify
from groq import Groq
import os
from dotenv import load_dotenv
import httpx
import asyncio

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

async def generate_image(prompt: str):
    if FAL_KEY is None:
        return None
    url = "https://54285744-flux-schnell.gateway.alpha.fal.ai"
    headers = {"Authorization": f"Key {FAL_KEY}"}
    payload = {
        "prompt": prompt + ", cute kawaii aesthetic, beautiful detailed, soft pastel colors, high quality",
        "image_size": "square_hd",
        "num_inference_steps": 4,
        "guidance_scale": 3.5,
        "sync_mode": True
    }
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(url, json=payload, headers=headers)
            r.raise_for_status()
            return r.json()["image"]["url"]
    except:
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
        for t in DRAW_TRIGGERS:
            prompt = prompt.replace(t, "").replace(t.capitalize(), "").replace(t.title(), "").strip()

        if len(prompt) < 3:
            prompt = "милая каваи девочка с розовыми волосами и большими глазами, аниме стиль, пастельные тона ♡"

        loop = asyncio.new_event_loop()
        image_url = loop.run_until_complete(generate_image(prompt))
        loop.close()

        if image_url:
            reply = f"Тадаааам!! Вот что я нарисовала для тебя\n\n![Busya рисунок]({image_url})"
        else:
            reply = "Ой-ой, картинка не получилась… Давай попробуем чуть позже, ладно? (⁠╥⁠﹏⁠╥⁠)"

    # === ОБЫЧНЫЙ ТЕКСТОВЫЙ ОТВЕТ ===
    else:
        try:
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
                ] + chat_history[-10:],
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
