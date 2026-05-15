from database import engine
from sqlalchemy import text

def activate_admin():
    try:
        with engine.connect() as conn:
            conn.execute(text("UPDATE users SET is_active = true, status = 'active' WHERE email = 'admin@test.com'"))
            conn.commit()
            print("✅ admin@test.com activé avec succès")
    except Exception as e:
        print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    activate_admin()