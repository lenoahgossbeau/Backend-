# test_quick.py
print("1. Test des imports...")
try:
    from models.user import User
    from models.refresh_token import RefreshToken
    print("✅ Modèles importés")
    
    # Vérifiez la relation
    if hasattr(User, 'refresh_tokens'):
        print("✅ User a la relation refresh_tokens")
    else:
        print("⚠️  User n'a PAS la relation refresh_tokens")
        
except Exception as e:
    print(f"❌ Erreur import: {e}")

print("\n2. Test base de données...")
try:
    from database import SessionLocal
    db = SessionLocal()
    
    # Simple requête
    from models.user import User
    users = db.query(User).all()
    print(f"✅ Base OK - Utilisateurs: {len(users)}")
    
    for u in users:
        print(f"   - {u.email} (ID: {u.id})")
    
    db.close()
except Exception as e:
    print(f"❌ Erreur base: {e}")