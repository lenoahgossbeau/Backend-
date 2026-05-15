from database import engine
from sqlalchemy import text

email = "activation.final@yopmail.com"

with engine.connect() as conn:
    conn.execute(text(f"UPDATE users SET is_active = true, status = 'active' WHERE email = '{email}'"))
    conn.commit()
    print(f"✅ Utilisateur {email} activé manuellement.")