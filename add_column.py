from sqlalchemy import text
from database import engine

def add_activation_code():
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN activation_code VARCHAR(100) DEFAULT NULL"))
            conn.commit()
            print("✅ Colonne 'activation_code' ajoutée avec succès.")
    except Exception as e:
        print("⚠️ La colonne existe peut-être déjà :", e)

if __name__ == "__main__":
    add_activation_code()