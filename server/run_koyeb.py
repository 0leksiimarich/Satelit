# run_koyeb.py — вхід для запуску (Koyeb/Render, Python web service, без Docker).
# Команда старту: uvicorn run_koyeb:app --host 0.0.0.0 --port $PORT
from app import app  # noqa: F401
