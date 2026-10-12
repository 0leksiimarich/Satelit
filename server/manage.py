# ============================================================
# manage.py — адміністрування даних «Сателіт».
# Запуск (у папці server/):
#   python manage.py admin EMAIL          — зробити користувача адміном
#   python manage.py resetpass EMAIL PW   — скинути пароль
#   python manage.py import FILE.xlsx     — імпорт товарів (без ШІ-перевірки)
#   python manage.py users                — список акаунтів
# ============================================================
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import (  # noqa: E402
    DB_LOCK, _load, hash_password, parse_table_bytes, write_db, _to_price,
    _to_int, _to_bool, _slugify, CATEGORY_ALIASES, CATEGORY_IDS, DEFAULT_IMAGE,
    norm_email,
)


def cmd_make_admin(email):
    email = norm_email(email)
    with DB_LOCK:
        data = _load()
        user = next((u for u in data["users"] if u["email"] == email), None)
        if not user:
            print("Користувач не знайдений. Спершу зареєструйтесь на сайті з цією поштою.")
            return
        user["isAdmin"] = True
        write_db(data)
    print("OK:", email, "— тепер адміністратор.")


def cmd_reset_pass(email, newpw):
    email = norm_email(email)
    with DB_LOCK:
        data = _load()
        user = next((u for u in data["users"] if u["email"] == email), None)
        if not user:
            print("Користувач не знайдений.")
            return
        user["passwordHash"] = hash_password(newpw)
        write_db(data)
    print("OK: пароль скинуто для", email)


def cmd_users():
    data = _load()
    if not data["users"]:
        print("Акаунтів ще немає.")
        return
    for u in data["users"]:
        flags = []
        if u.get("isAdmin"):
            flags.append("адмін")
        if u.get("blocked"):
            flags.append("заблоковано")
        print(f"{u['email']}  {u.get('name', '')}  {' '.join(flags)}")


def cmd_import(path):
    with open(path, "rb") as f:
        raw = f.read()
    rows = parse_table_bytes(path, raw)
    added = 0
    with DB_LOCK:
        data = _load()
        for r in rows:
            name = str(r.get("name") or "").strip()
            if not name:
                continue
            try:
                price = _to_price(r.get("price"))
            except ValueError:
                continue
            cat_raw = str(r.get("category") or "").strip().lower()
            category = CATEGORY_ALIASES.get(cat_raw, cat_raw if cat_raw in CATEGORY_IDS else "other")
            pid = "imp-" + _slugify(name)
            product = {
                "id": pid,
                "name": name,
                "description": str(r.get("description") or "").strip(),
                "price": round(price, 2),
                "category": category,
                "image": str(r.get("image") or "").strip() or DEFAULT_IMAGE,
                "stock": max(_to_int(r.get("stock")), 0),
                "featured": _to_bool(r.get("featured")),
                "sale": _to_bool(r.get("sale")),
            }
            data["products"] = [p for p in data["products"] if p["id"] != pid] + [product]
            added += 1
        write_db(data)
    print(f"OK: імпортовано {added} товарів із {path}.")


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) >= 2 and args[0] == "admin":
        cmd_make_admin(args[1])
    elif len(args) >= 3 and args[0] == "resetpass":
        cmd_reset_pass(args[1], args[2])
    elif len(args) >= 2 and args[0] == "import":
        cmd_import(args[1])
    elif args and args[0] == "users":
        cmd_users()
    else:
        print(__doc__)
