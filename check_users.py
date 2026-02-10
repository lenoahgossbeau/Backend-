# check_users.py
from database import SessionLocal
from models.user import User

db = SessionLocal()
users = db.query(User).all()

print("Nombre d'utilisateurs:", len(users))
if users:
    for u in users:
        print(f"  - {u.email} (ID: {u.id}, Role: {u.role}, Status: {u.status})")
else:
    print("Aucun utilisateur trouve")

db.close()