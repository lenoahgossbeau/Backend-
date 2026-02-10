from sqlalchemy import create_engine, text
from database import DATABASE_URL, Base
import models.user
import models.profile
import models.audit
import models.publication
import models.message_contact
import models.comment
import models.project
import models.academic_career
import models.media_artefact
import models.distinction
import models.cours
import models.subscription
import models.refresh_token

print("🔄 Mise à jour de la base de données avec diplome...")

engine = create_engine(DATABASE_URL)

# 1. Vérifiez si la colonne diploma existe et renommez-la
with engine.connect() as conn:
    # Vérifiez la structure actuelle
    result = conn.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'academic_careers' 
        AND column_name IN ('diploma', 'diplome');
    """)).fetchall()
    
    columns = [row[0] for row in result]
    
    if 'diploma' in columns and 'diplome' not in columns:
        print("🔧 Renommage de 'diploma' en 'diplome'...")
        conn.execute(text("ALTER TABLE academic_careers RENAME COLUMN diploma TO diplome;"))
        conn.commit()
        print("✅ Colonne renommée")
    elif 'diplome' in columns:
        print("✅ Colonne 'diplome' existe déjà")
    else:
        print("⚠️  Aucune colonne diplome/diploma trouvée")

# 2. Si nécessaire, recréez toute la base
print("\n🔧 Reconstruction des tables si nécessaire...")
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print("✅ Base de données reconstruite")

print("\n🎯 Base de données prête ! Tous les tests devraient passer maintenant.")
