# ============================================================
# server/app.py — «Сателіт Backend»: власна заміна Firebase/Supabase
# Python + FastAPI. Хостинг: Render.com (безкоштовно).
#
# Ендпоінти:
#   /api/health                — перевірка чи сервер живий
#   /api/auth/otp/send         — надіслати одноразовий код на email
#   /api/auth/register         — реєстрація (ім'я, телефон, пароль + код)
#   /api/auth/login            — вхід
#   /api/auth/me               — хто я (за токеном)
#   /api/products              — товари
#   /api/orders                — створити замовлення / побачити свої
#   /api/admin/*               — усе для адміна (замовлення, імпорт товарів)
#
# Пошта служби підтримки: satelit-magazin@ukr.net
# Дані: JSON-файл на диску (SATELIT_DATA_DIR=/var/data + Disk на Render).
# ============================================================

import os
import re
import json
import time
import hmac
import hashlib
import secrets
import threading
from datetime import datetime, timezone

import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Satelit Backend", version="1.0")

# Дозволити запитувати сервер з GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Сховище даних (простий JSON-файл; simpledatastore більше НЕ використовується) ----------
DATA_DIR = os.environ.get("SATELIT_DATA_DIR", "data")
DATA_FILE = os.environ.get("SATELIT_DATA_FILE", os.path.join(DATA_DIR, "satelit_data.json"))
_lock = threading.Lock()

DEFAULT_DATA = {"users": [], "products": [], "orders": [], "tokens": {}, "otps": []}

def _load():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return json.loads(json.dumps(DEFAULT_DATA))

def _save(data):
    # Атомарний запис: спершу у тимчасовий файл, потім перевідменування.
    d = os.path.dirname(DATA_FILE) or "."
    os.makedirs(d, exist_ok=True)
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)

def db():
    with _lock:
        return _load()

def write_db(data):
    with _lock:
        _save(data)

# ---------- Паролі (PBKDF2 — безпечно, стандартна бібліотека) ----------
def hash_password(pw):
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), 100_000)
    return salt + ":" + h.hex()

def verify_password(pw, stored):
    try:
        salt, h = stored.split(":")
        return hmac.compare_digest(
            hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), 100_000).hex(), h)
    except Exception:
        return False

# ---------- Токени сесії ----------
SECRET = os.environ.get("SATELIT_SECRET", "dev-secret-change-me")

def make_token(user_id):
    ts = str(int(time.time()))
    sig = hmac.new(SECRET.encode(), (user_id + "." + ts).encode(), hashlib.sha256).hexdigest()[:32]
    return user_id + "." + ts + "." + sig

def parse_token(token):
    try:
        uid, ts, sig = token.rsplit(".", 2)
        expect = hmac.new(SECRET.encode(), (uid + "." + ts).encode(), hashlib.sha256).hexdigest()[:32]
        if not hmac.compare_digest(sig, expect):
            return None
        if time.time() - int(ts) > 60 * 60 * 24 * 30:  # 30 днів
            return None
        return uid
    except Exception:
        return None

def current_user(request):
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "").strip()
    uid = parse_token(token) if token else None
    if not uid:
        raise HTTPException(401, "Увійдіть в акаунт.")
    data = db()
    u = next((x for x in data["users"] if x["id"] == uid), None)
    if not u:
        raise HTTPException(401, "Сесія некоректна. Увійдіть ще раз.")
    return u

def require_admin(request):
    u = current_user(request)
    if not u.get("is_admin"):
        raise HTTPException(403, "Потрібні права адміністратора.")
    return u

# ---------- Пошта служби підтримки ----------
SUPPORT_EMAIL = os.environ.get("SATELIT_SUPPORT_EMAIL", "satelit-magazin@ukr.net")

# ---------- ШІ-перевірка товарів (OpenRouter, модель gemma) ----------
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "google/gemma-4-31b-it:free")

def ai_review_product(p):
    """Перевіряє рядок таблиці через ШІ gemma.
    ok=None — ключа немає або ШІ недоступний (додати без перевірки)."""
    if not OPENROUTER_API_KEY:
        return {"ok": None, "reason": "", "description": "", "category": ""}
    prompt = (
        "Ти перевіряєш дані товару для інтернет-магазину електроніки «Сателіт» (Шпола).\n"
        "Категорії: batteries, tvbox, antennas, cables, accessories, other.\n"
        "Товар: назва «{name}», ціна {price} грн, категорія «{cat}», залишок {stock}.\n"
        "Відповідь — ТІЛЬКИ валідний JSON без зайвого тексту:\n"
        '{{"ok": true/false, "reason": "коротко чому ні (українською)" або "", '
        '"description": "1-2 речення маркетингового опису українською, без вигаданих характеристик", '
        '"category": "правильна англійська категорія зі списку вище"}}\n'
        "ok=false, якщо назва порожня/безглузда, ціна не відповідає типу товару "
        "або рядок схожий на сміття."
    ).format(name=p["name"], price=p["price"], cat=p["category"], stock=p["stock"])
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": "Bearer " + OPENROUTER_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "model": OPENROUTER_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            },
            timeout=30,
        )
        if not r.ok:
            print("OpenRouter error:", r.status_code, r.text[:200])
            return {"ok": None, "reason": "", "description": "", "category": ""}
        text = r.json()["choices"][0]["message"]["content"].strip()
        m = re.search(r"\{.*\}", text, re.S)
        verdict = json.loads(m.group(0)) if m else {}
        return {
            "ok": bool(verdict.get("ok", True)),
            "reason": str(verdict.get("reason", ""))[:200],
            "description": str(verdict.get("description", ""))[:500],
            "category": str(verdict.get("category", "")).strip().lower(),
        }
    except Exception as e:
        print("AI review failed:", e)
        return {"ok": None, "reason": "", "description": "", "category": ""}

# ---------- Імпорт товарів із файлу таблиці (.xlsx/.xls/.csv) ----------
CATEGORY_ALIASES = {
    "батарейки": "batteries", "battery": "batteries", "batteries": "batteries",
    "tv box": "tvbox", "tvbox": "tvbox", "тв бокс": "tvbox", "телевізор": "tvbox",
    "антени": "antennas", "antenna": "antennas", "antennas": "antennas",
    "кабелі": "cables", "кабели": "cables", "cable": "cables", "cables": "cables",
    "аксесуари": "accessories", "аксессуары": "accessories", "accessories": "accessories",
    "інше": "other", "иное": "other", "other": "other", "інша техніка": "other",
}

COLMAP = {
    "name": ["name", "назва", "найменування", "товар", "product", "title"],
    "price": ["price", "ціна", "цена", "cost"],
    "category": ["category", "категорія", "категория", "група"],
    "description": ["description", "опис", "описание", "desc"],
    "image": ["image", "фото", "зображення", "img", "picture"],
    "stock": ["stock", "залишок", "кількість", "остаток", "qty", "quantity"],
    "featured": ["featured", "популярний", "рекомендований"],
    "sale": ["sale", "акція", "акційний"],
}

def _norm_header(h):
    return str(h or "").strip().lower().replace("\u00a0", " ")

def _map_columns(headers):
    mapping = {}
    for i, h in enumerate(headers):
        n = _norm_header(h)
        for field, aliases in COLMAP.items():
            if any(a == n or a in n for a in aliases) and field not in mapping:
                mapping[field] = i
                break
    return mapping

def _to_bool(v):
    s = str(v or "").strip().lower()
    return s in ("1", "true", "yes", "так", "y", "плюс", "+")

def parse_table_bytes(filename, raw):
    """Повертає список рядків-товарів із .xlsx/.xls/.csv."""
    import io
    ext = filename.lower().rsplit(".", 1)[-1]
    rows = []
    if ext in ("xlsx", "xlsm"):
        from openpyxl import load_workbook
        wb = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
        ws = wb.active
        it = ws.iter_rows(values_only=True)
        headers = next(it, None)
        if not headers:
            raise HTTPException(400, "Файл порожній.")
        mapping = _map_columns(headers)
        for row in it:
            if row is None or all(v is None or str(v).strip() == "" for v in row):
                continue
            rows.append({k: (row[i] if i < len(row) else None) for k, i in mapping.items()})
    elif ext == "xls":
        import pandas as pd
        df = pd.read_excel(io.BytesIO(raw))
        mapping = _map_columns(list(df.columns))
        for _, r in df.iterrows():
            rows.append({k: r.iloc[i] for k, i in mapping.items()})
    elif ext in ("csv", "txt"):
        import csv as _csv
        enc = "utf-8-sig"
        try:
            sample = raw.decode(enc)
        except UnicodeDecodeError:
            enc = "cp1251"
            sample = raw.decode(enc)
        delim = ";" if sample.count(";") > sample.count(",") else ","
        reader = _csv.reader(io.StringIO(sample), delimiter=delim)
        rowslist = [r for r in reader if any(str(c).strip() for c in r)]
        if not rowslist:
            raise HTTPException(400, "CSV порожній.")
        mapping = _map_columns(rowslist[0])
        for r in rowslist[1:]:
            rows.append({k: (r[i] if i < len(r) else None) for k, i in mapping.items()})
    else:
        raise HTTPException(400, "Потрібен файл .xlsx, .xls або .csv.")
    if not rows:
        raise HTTPException(400, "У файлі немає рядків з даними.")
    return rows

def _slugify(text):
    s = re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")
    return s[:40] or secrets.token_hex(4)

VALID_CATS = {"batteries", "tvbox", "antennas", "cables", "accessories", "other"}

# ---------- Одноразові коди (OTP) ----------
OTP_TTL = 15 * 60          # код дійсний 15 хвилин
OTP_RESEND_AFTER = 60      # повторна відправка не раніше ніж через 60 с
MAX_OTP_ATTEMPTS = 5       # спроб введення коду на один запит

def gen_otp():
    return f"{secrets.randbelow(1000000):06d}"   # 6-значний код

def otp_issue(data, email, purpose):
    now = time.time()
    for rec in data.get("otps", []):
        if rec["email"] == email and rec["purpose"] == purpose:
            if now - rec["created_at"] < OTP_RESEND_AFTER and not rec.get("consumed"):
                raise HTTPException(429, "Код уже надіслано. Зачекайте хвилину й повторіть.")
            rec.update(code=gen_otp(), created_at=now, attempts=0, consumed=False)
            return rec["code"]
    code = gen_otp()
    data.setdefault("otps", []).append({
        "email": email, "purpose": purpose, "code": code,
        "created_at": now, "attempts": 0, "consumed": False})
    return code

def otp_verify(data, email, purpose, code):
    rec = next((r for r in data.get("otps", [])
                if r["email"] == email and r["purpose"] == purpose and not r.get("consumed")), None)
    if not rec:
        raise HTTPException(400, "Спершу отримайте код на пошту (кнопка «Отримати код»).")
    if time.time() - rec["created_at"] > OTP_TTL:
        raise HTTPException(400, "Код прострочено (15 хвилин). Надішліть новий.")
    if rec.get("attempts", 0) >= MAX_OTP_ATTEMPTS:
        raise HTTPException(400, "Забагато невдалих спроб. Надішліть новий код.")
    if str(code).strip() != rec["code"]:
        rec["attempts"] = rec.get("attempts", 0) + 1
        write_db(data)
        raise HTTPException(400, "Невірний код. Перевірте цифри з листа.")
    rec["consumed"] = True
    return rec

# ---------- SMTP (листалка). Без нього — демо-режим (код показується на сайті) ----------
SMTP_HOST = os.environ.get("SMTP_HOST", "")          # smtp.ukr.net
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))
SMTP_USER = os.environ.get("SMTP_USER", "")          # satelit-magazin@ukr.net
SMTP_PASS = os.environ.get("SMTP_PASS", "")          # пароль до скриньки ukr.net
SMTP_FROM = os.environ.get("SMTP_FROM", SMTP_USER or SUPPORT_EMAIL)

def send_email(to, subject, text):
    if not SMTP_HOST or not SMTP_USER or not SMTP_PASS:
        print(f"[DEMO] лист {to} ({subject}): {text}")
        return "demo"
    try:
        import smtplib
        from email.mime.text import MIMEText
        msg = MIMEText(text, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = SMTP_FROM
        msg["To"] = to
        if SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=20)
        else:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20)
            server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, [to], msg.as_string())
        server.quit()
        return "sent"
    except Exception as e:
        print("send_email failed:", e)
        return "failed"

# ---------- Моделі даних ----------
class OtpSendIn(BaseModel):
    email: str
    purpose: str = "register"    # register | login

class RegisterIn(BaseModel):
    email: str
    password: str
    name: str      # Ім'я та прізвище — обов'язково
    phone: str     # Номер телефону — обов'язково
    code: str      # одноразовий код із листа

class LoginIn(BaseModel):
    email: str
    password: str
    code: str = ""

class OrderItem(BaseModel):
    id: str
    name: str
    price: float
    qty: int

class OrderIn(BaseModel):
    items: list[OrderItem]
    total: float
    delivery_method: str
    customer_name: str
    phone: str
    address: str = ""

class StatusIn(BaseModel):
    status: str

class ProductIn(BaseModel):
    id: str
    name: str
    description: str = ""
    price: float
    category: str
    image: str = "assets/img-placeholder.svg"
    stock: int = 0
    featured: bool = False
    sale: bool = False

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
STATUSES = ["Нове", "Підтверджено", "Готується", "Відправлено", "Виконано", "Скасовано"]

# ---------- Ендпоінти ----------
@app.get("/api/health")
def health():
    return {"ok": True, "time": datetime.now(timezone.utc).isoformat()}

@app.post("/api/auth/otp/send")
def otp_send(body: OtpSendIn):
    """Надсилає одноразовий 6-значний код на email."""
    email = body.email.strip().lower()
    purpose = body.purpose if body.purpose in ("register", "login") else "register"
    if not EMAIL_RE.match(email):
        raise HTTPException(400, "Некоректна email-адреса.")
    data = db()
    exists = any(u["email"] == email for u in data["users"])
    if purpose == "register" and exists:
        raise HTTPException(400, "Ця email-адреса вже використовується.")
    if purpose == "login" and not exists:
        raise HTTPException(400, "Користувача з такою адресою не знайдено.")
    code = otp_issue(data, email, purpose)
    write_db(data)
    status = send_email(
        email,
        f"Сателіт — ваш одноразовий код: {code}",
        "Ваш одноразовий код для «Сателіт»: " + code +
        "\nКод дійсний 15 хвилин. Нікому не повідомляйте його."
    )
    if status == "failed":
        raise HTTPException(502, "Не вдалося надіслати лист. Спробуйте пізніше.")
    return {"ok": True, "demoCode": code if status == "demo" else None}

@app.post("/api/auth/register")
def register(body: RegisterIn):
    email = body.email.strip().lower()
    full_name = " ".join(body.name.split())
    phone = body.phone.strip()
    if not EMAIL_RE.match(email):
        raise HTTPException(400, "Некоректна email-адреса.")
    if len(body.password) < 6:
        raise HTTPException(400, "Пароль занадто короткий (мінімум 6 символів).")
    if len(full_name) < 3 or " " not in full_name:
        raise HTTPException(400, "Вкажіть ім'я та прізвище повністю.")
    if not re.match(r"^\+?[\d\s()-]{9,}$", phone):
        raise HTTPException(400, "Вкажіть коректний номер телефону.")
    data = db()
    if any(u["email"] == email for u in data["users"]):
        raise HTTPException(400, "Ця email-адреса вже використовується.")
    otp_verify(data, email, "register", body.code)   # без підтвердження поштою — не зареєструєш
    user = {
        "id": "u_" + secrets.token_hex(8),
        "email": email,
        "password_hash": hash_password(body.password),
        "display_name": full_name,
        "phone": phone,
        "is_admin": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    data["users"].append(user)
    write_db(data)
    return {"token": make_token(user["id"]), "user": public_user(user)}

@app.post("/api/auth/login")
def login(body: LoginIn):
    email = body.email.strip().lower()
    data = db()
    user = next((u for u in data["users"] if u["email"] == email), None)
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(400, "Неправильна email-адреса або пароль.")
    pending = next((r for r in data.get("otps", [])
                    if r["email"] == email and r["purpose"] == "login"
                    and not r.get("consumed")), None)
    if pending:
        otp_verify(data, email, "login", body.code)
    write_db(data)
    return {"token": make_token(user["id"]), "user": public_user(user)}

@app.post("/api/auth/logout")
def logout():
    return {"ok": True}

@app.get("/api/auth/me")
def me(request: Request):
    return {"user": public_user(current_user(request))}

def public_user(u):
    return {"id": u["id"], "email": u["email"],
            "displayName": u.get("display_name", ""),
            "phone": u.get("phone", ""),
            "isAdmin": bool(u.get("is_admin")),
            "supportEmail": SUPPORT_EMAIL}

@app.get("/api/products")
def products():
    data = db()
    if not data["products"]:
        return {"products": DEMO_PRODUCTS}
    return {"products": data["products"]}

DEMO_PRODUCTS = [
    {"id": "demo-tvbox-1", "name": "[Приклад] TV Box Android 4K",
     "description": "Демонстраційна картка товару. Замінити на реальний товар.",
     "price": 1299, "category": "tvbox", "image": "assets/img-placeholder.svg",
     "stock": 0, "featured": True, "sale": False},
    {"id": "demo-battery-1", "name": "[Приклад] Батарейки AA, 4 шт.",
     "description": "Демонстраційна картка товару. Замінити на реальний товар.",
     "price": 59, "category": "batteries", "image": "assets/img-placeholder.svg",
     "stock": 0, "featured": True, "sale": False},
    {"id": "demo-antenna-1", "name": "[Приклад] Антена цифрова DVB-T2",
     "description": "Демонстраційна картка товару. Замінити на реальний товар.",
     "price": 349, "category": "antennas", "image": "assets/img-placeholder.svg",
     "stock": 0, "featured": False, "sale": False},
    {"id": "demo-cable-1", "name": "[Приклад] Кабель HDMI 2 м",
     "description": "Демонстраційна картка товару. Замінити на реальний товар.",
     "price": 149, "category": "cables", "image": "assets/img-placeholder.svg",
     "stock": 0,
