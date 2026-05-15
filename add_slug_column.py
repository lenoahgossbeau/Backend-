from database import engine
from sqlalchemy import text

def add_slug_column():
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN slug VARCHAR(100) UNIQUE"))
            conn.commit()
            print("✅ Colonne 'slug' ajoutée avec succès")
    except Exception as e:
        print(f"⚠️ La colonne existe peut-être déjà : {e}")

if __name__ == "__main__":
    add_slug_column()