from flask import Flask, request, jsonify
# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
# СЮДА импортируешь всё своё (модель, функции и т.д.)
from my_super_ai import get_ai_response   # например
# ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def main():
    if request.method == "GET":
        return jsonify({"status": "ok", "message": "Твой ИИ жив!"})    
    
    if request.method == "POST":
        data = request.get_json(force=True)        # ← твой входной json
        user_message = data.get("message", "")     # ← подстрой под свою структуру
        
        # ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
        # СЮДА вставляешь вызов своего ИИ
        ai_answer = get_ai_response(user_message)
        # ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑
        
        return jsonify({"response": ai_answer})

# Эту строку НЕ УДАЛЯЙ — Vercel без неё не запустит Flask
__vercel_app__ = app
