# create_admin.py - VERSION FONCTIONNELLE
print("="*50)
print("CRÉATION D'UN COMPTE ADMIN")
print("="*50)

# 1. IMPORTATION STRATÉGIQUE - IMPORTEZ D'ABORD LES MODÈLES
print("📦 Importation des modèles...")

# Importez d'abord la base
from database import Base

# Importez TOUS vos modèles (l'ordre est important)
import models.user          # Importe User
import models.profile       # Importe Profile  
import models.audit         # Importe Audit
import models.refresh_token # Importe RefreshToken
import models.publication   # Importe Publication

# Importez maintenant ce dont vous avez besoin
from sqlalchemy.orm import Session
import hashlib
from datetime import datetime

print("✅ Modèles importés")

# 2. Hachage du mot de passe
def simple_hash(password: str) -> str:
    """Hash SHA256 simple pour les tests"""
    return hashlib.sha256(password.encode()).hexdigest()

# 3. Connexion à la base
print("🔌 Connexion à la base de données...")
from database import SessionLocal
db = SessionLocal()

print("✅ Base connectée")

# 4. Importez User MAINTENANT (après tous les modèles)
from models.user import User

# 5. Vérifier si admin existe
print("\n🔍 Vérification si l'admin existe déjà...")
existing_admin = db.query(User).filter(User.email == "admin@test.com").first()

if existing_admin:
    print(f"\n✅ ADMIN EXISTE DÉJÀ")
    print(f"   📧 Email: {existing_admin.email}")
    print(f"   👑 Rôle: {existing_admin.role}")
    print(f"   📊 Statut: {existing_admin.status}")
    print(f"   🆔 ID: {existing_admin.id}")
else:
    # 6. Créer le nouvel admin
    print("\n👤 Création du nouvel admin...")
    
    admin = User(
        email="admin@test.com",
        password=simple_hash("admin123"),  # Mot de passe: admin123
        role="admin",
        status="active"
    )
    
    try:
        db.add(admin)
        db.commit()
        db.refresh(admin)  # Pour obtenir l'ID
        
        print(f"\n🎉 ADMIN CRÉÉ AVEC SUCCÈS!")
        print(f"   📧 Email: {admin.email}")
        print(f"   🔑 Mot de passe: admin123")
        print(f"   👑 Rôle: {admin.role}")
        print(f"   📊 Statut: {admin.status}")
        print(f"   🆔 ID: {admin.id}")
        
        print("\n💾 Sauvegarde effectuée dans la base de données")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ ERREUR lors de la création: {e}")
        print("Vérifiez que:")
        print("1. PostgreSQL est démarré")
        print("2. La base 'inchtechs_db' existe")
        print("3. La table 'users' existe")

# 7. Fermer la connexion
db.close()

print("\n" + "="*50)
print("OPÉRATION TERMINÉE")
print("="*50)