from database import engine
from sqlalchemy import text

def add_recipient_column():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE contact_messages ADD COLUMN recipient_user_id INTEGER"))
            conn.commit()
            print("✅ Colonne 'recipient_user_id' ajoutée avec succès")
        except Exception as e:
            print(f"⚠️ La colonne existe peut-être déjà : {e}")

if __name__ == "__main__":
    add_recipient_column()