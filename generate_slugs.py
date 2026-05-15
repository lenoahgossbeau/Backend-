from database import engine
from sqlalchemy import text
import re

def slugify(name):
    return re.sub(r'[^a-z0-9-]', '-', name.lower()).strip('-')

with engine.connect() as conn:
    users = conn.execute(text("SELECT u.id, u.email, p.first_name, p.last_name FROM users u LEFT JOIN profiles p ON u.id = p.user_id WHERE u.role = 'researcher'"))
    for row in users:
        first = row.first_name or ''
        last = row.last_name or ''
        if first or last:
            slug = slugify(f"{first}-{last}")
        else:
            slug = slugify(row.email.split('@')[0])
        
        # S'assurer que le slug est unique
        base_slug = slug
        counter = 1
        while True:
            existing = conn.execute(text(f"SELECT id FROM users WHERE slug = '{slug}' AND id != {row.id}")).first()
            if not existing:
                break
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        conn.execute(text(f"UPDATE users SET slug = '{slug}' WHERE id = {row.id}"))
        print(f"ID {row.id} ({row.email}) → {slug}")
    
    conn.commit()
    print("✅ Slugs générés")