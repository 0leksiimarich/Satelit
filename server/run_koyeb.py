# run_koyeb.py — вхідна точка для запуску (Koyeb/Render).
# Команда старту: uvicorn run_koyeb:app --host 0.0.0.0 --port $PORT
from app import app  # noqa: F401
