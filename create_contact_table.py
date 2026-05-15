from database import engine
from models.contact_message import ContactMessage

def create_table():
    try:
        ContactMessage.metadata.create_all(bind=engine)
        print("✅ Table 'contact_messages' créée avec succès")
    except Exception as e:
        print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    create_table()