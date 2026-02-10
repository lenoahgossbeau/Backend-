#!/usr/bin/env python3
"""
SCRIPT DE RÉPARATION DE LA BASE DE DONNÉES
Exécute ce script APRÈS avoir corrigé tous les modèles
"""
import os
import sys

# Ajouter le répertoire courant au chemin Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🔧 DÉMARRAGE DE LA RÉPARATION DE LA BASE DE DONNÉES")
print("="*60)

try:
    # 1. Importer les modules nécessaires
    from sqlalchemy import create_engine, text
    from database import Base, engine
    from init_db import init_db
    
    print("✅ Modules importés avec succès")
    
    # 2. Obtenir la liste des tables existantes
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """))
        tables = [row[0] for row in result]
        
        if tables:
            print(f"📋 Tables existantes: {', '.join(tables)}")
        else:
            print("📋 Aucune table existante")
    
    # 3. Demander confirmation
    print("\n⚠️  ATTENTION: Cette opération va SUPPRIMER toutes les données existantes!")
    confirmation = input("Continuer? (oui/non): ")
    
    if confirmation.lower() != 'oui':
        print("❌ Opération annulée")
        sys.exit(0)
    
    # 4. Supprimer toutes les tables
    print("\n🗑️  Suppression des tables...")
    with engine.connect() as conn:
        # Désactiver temporairement les contraintes
        conn.execute(text("SET session_replication_role = 'replica';"))
        
        # Supprimer les tables dans le bon ordre (éviter les erreurs de contraintes)
        tables_to_drop = [
            'academic_careers',
            'media_artefacts',
            'distinctions',
            'cours',
            'publications',
            'projects',
            'messages_contact',
            'comments',
            'subscriptions',
            'audits',
            'refresh_tokens',
            'profiles',
            'users'
        ]
        
        for table in tables_to_drop:
            try:
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
                print(f"   ✅ Table {table} supprimée")
            except Exception as e:
                print(f"   ⚠️  {table}: {str(e)[:50]}...")
        
        # Réactiver les contraintes
        conn.execute(text("SET session_replication_role = 'origin';"))
        conn.commit()
    
    print("\n✅ Toutes les tables supprimées")
    
    # 5. Recréer la base de données
    print("\n🏗️  Recréation de la base de données...")
    init_db()
    
    print("\n" + "="*60)
    print("🎉 BASE DE DONNÉES RÉPARÉE AVEC SUCCÈS !")
    print("="*60)
    print("\n📋 ÉTAPES SUIVANTES:")
    print("1. Lance les tests: pytest tests/test_models.py -v")
    print("2. Lance l'application: uvicorn main:app --reload")
    print("3. Teste: http://localhost:8000/portfolio")
    print("="*60)
    
except Exception as e:
    print(f"\n❌ ERREUR CRITIQUE: {e}")
    import traceback
    traceback.print_exc()
    
    print("\n🔧 SOLUTION DE SECOURS:")
    print("1. Supprime manuellement le fichier de base de données (portfolio.db)")
    print("2. Exécute: python init_db.py")
    print("3. Relance l'application")

# Mode interactif pour les utilisateurs Windows
if os.name == 'nt':  # Windows
    input("\nAppuyez sur Entrée pour quitter...")