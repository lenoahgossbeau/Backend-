import sys
import os
import bcrypt
from sqlalchemy.orm import Session

# Ajouter le chemin du projet Portfolio au sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, Base
# ⚠️ Importer tous les modèles pour que SQLAlchemy connaisse les relations
import models.user
import models.audit
import models.profile
import models.publication
import models.refresh_token

# Connexion à la base
db: Session = SessionLocal()

# Hachage du mot de passe "admin"
hashed = bcrypt.hashpw("admin".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

# Création de l'utilisateur admin
admin = models.user.User(
    email="admin@example.com",
    password=hashed,
    role="admin",
    status="active"
)

# Insertion dans la base
db.add(admin)
db.commit()
db.close()

print("✅ Utilisateur admin inséré avec succès")
