# Утиліта адміністрування даних «Сателіт Backend».
# Запуск: python manage.py <команда>
import sys, json, secrets
sys.path.insert(0, ".")
from app import db, write_db, hash_password, parse_table_bytes

def cmd_make_admin(email):
    email = email.strip().lower()
    data = db()
    u = next((x for x in data["users"] if x["email"] == email), None)
    if not u:
        print("Користувач не знайдений. Спершу зареєструйтесь на сайті з цією поштою."); return
    u["is_admin"] = True
    write_db(data)
    print("OK:", email, "— тепер адміністратор.")

def cmd_import(path):
    """Імпорт товарів із таблиці напряму: python manage.py import products.xlsx"""
    with open(path, "rb") as f:
        raw = f.read()
    rows = parse_table_bytes(path, raw)
    data = db()
    n = 0
    for row in rows:
        name = str(row.get("name") or "").strip()
        if not name:
            continue
        try:
            price = float(str(row.get("price", "")).replace(",", ".").replace("\u20b4", "").strip())
        except (TypeError, ValueError):
            continue
        pid = "imp-" + name.lower()[:30].replace(" ", "-")
        product = {
            "id": pid, "name": name,
            "description": str(row.get("description") or "").strip(),
            "price": price,
            "category": str(row.get("category") or "other").strip().lower(),
            "image": str(row.get("image") or "assets/img-placeholder.svg").strip(),
            "stock": int(float(row.get("stock") or 0)),
            "featured": str(row.get("featured") or "").lower() in ("1", "true", "так"),
            "sale": str(row.get("sale") or "").lower() in ("1", "true", "так"),
        }
        data["products"] = [x for x in data["products"] if x["id"] != pid] + [product]
        n += 1
    write_db(data)
    print(f"OK: імпортовано {n} товарів із {path}.")

def cmd_reset_pass(email, newpw):
    email = email.strip().lower()
    data = db()
    u = next((x for x in data["users"] if x["email"] == email), None)
    if not u:
        print("Користувач не знайдений."); return
    u["password_hash"] = hash_password(newpw)
    write_db(data)
    print("OK: пароль скинуто для", email)

if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "admin":
        cmd_make_admin(sys.argv[2])
    elif len(sys.argv) >= 4 and sys.argv[1] == "resetpass":
        cmd_reset_pass(sys.argv[2], sys.argv[3])
    elif len(sys.argv) >= 3 and sys.argv[1] == "import":
        cmd_import(sys.argv[2])
    else:
        print("Команди:\n  python manage.py admin EMAIL\n  python manage.py resetpass EMAIL PW\n  python manage.py import FILE.(xlsx|xl
