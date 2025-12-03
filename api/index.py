# api/index.py
from app import app as application  # импортируем готовое приложение из твоего app.py

# ЭТО САМАЯ ВАЖНАЯ СТРОКА ДЛЯ VERCEL
__vercel_app__ = application

# ←←←←←←←←←←←←←←←←←←←←
