from database import engine
from sqlalchemy import text
import bcrypt

email = "jean.dupont1@test.com"
new_password = "12345678"

hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

with engine.connect() as conn:
    conn.execute(text(f"UPDATE users SET password = '{hashed}', is_active = true, status = 'active' WHERE email = '{email}'"))
    conn.commit()
    print(f"✅ Mot de passe de {email} réinitialisé à {new_password} et compte activé")