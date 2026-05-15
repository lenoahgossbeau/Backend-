from database import engine
from sqlalchemy import text

print("=== DERNIERS MESSAGES ===")
with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM contact_messages ORDER BY id DESC LIMIT 5"))
    for row in result:
        print(f"id={row.id}, name={row.name}, email={row.email}, recipient_user_id={row.recipient_user_id}, message={row.message[:50]}...")

print("\n=== CHERCHEURS ===")
with engine.connect() as conn:
    result = conn.execute(text("SELECT id, email FROM users WHERE role = 'researcher' AND is_active = true"))
    for row in result:
        print(f"id={row.id}, email={row.email}")