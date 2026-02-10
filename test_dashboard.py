# test_dashboard.py - COPIEZ TOUT CE CODE
print("="*60)
print("TEST DU DASHBOARD ADMIN")
print("="*60)

print("\n📋 CE QUE CE SCRIPT FAIT:")
print("Teste si votre dashboard admin fonctionne")

print("\n⚡ PRÉ-REQUIS:")
print("1. Admin créé? Exécutez: python create_admin.py")
print("2. Token obtenu? Exécutez: python get_token.py")
print("3. Serveur démarré? Exécutez: uvicorn main:app --reload")

print("\n🔑 ÉTAPE 1: OBTENIR UN TOKEN")
print("-"*40)
print("1. Exécutez: python get_token.py")
print("2. Copiez le token qui s'affiche (longue chaîne)")
print("3. Collez-le ci-dessous à la place de 'TON_TOKEN'")

# ========== COLLEZ VOTRE TOKEN ICI ==========
TON_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzIiwicm9sZSI6ImFkbWluIiwiZXhwIjoxNzcwMTY1NDA4fQ.UVsKHEZwZZ9cNG_FUrJm0-n1XFrI68IPV5_RecOEMLQ"
# ========== EXEMPLE: TON_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5c..." ==========

if TON_TOKEN == "TON_TOKEN":
    print("\n❌ ERREUR: Vous devez coller votre token!")
    print("\n📝 COMMENT FAIRE:")
    print("1. Exécutez: python get_token.py")
    print("2. Copiez le token (ex: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...)")
    print("3. Ouvrez ce fichier dans VS Code")
    print("4. Trouvez la ligne: TON_TOKEN = \"TON_TOKEN\"")
    print("5. Remplacez \"TON_TOKEN\" par votre vrai token")
    print("6. Sauvegardez (Ctrl+S)")
    exit()

print(f"\n✅ Token reçu: {TON_TOKEN[:30]}...")
print("\n🧪 DÉBUT DES TESTS...")
print("="*60)

# Cette partie teste votre dashboard
try:
    import requests
    print("✅ Bibliothèque 'requests' importée")
    
    # Préparer les headers avec votre token
    headers = {"Authorization": f"Bearer {TON_TOKEN}"}
    
    # Liste des URLs à tester
    urls = [
        ("📊 Audits", "http://localhost:8000/admin/audits", headers),
        ("📄 PDF", "http://localhost:8000/admin/dashboard/export/pdf", headers),
        ("📈 CSV", "http://localhost:8000/admin/dashboard/export/csv", headers),
        ("📊 Stats", "http://localhost:8000/admin/audit-stats", headers),
        ("🏠 Accueil", "http://localhost:8000/", {}),  # Pas besoin de token
    ]
    
    for nom, url, use_headers in urls:
        print(f"\n🧪 Test: {nom}")
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url, headers=use_headers, timeout=5)
            
            if response.status_code == 200:
                print(f"   ✅ SUCCÈS (Code: 200)")
                
                if "csv" in url:
                    print(f"   📁 Fichier CSV: {len(response.content)} octets")
                elif "pdf" in url:
                    # Vérifier si c'est du JSON (mock) ou un PDF
                    content_type = response.headers.get('content-type', '')
                    if 'json' in content_type:
                        data = response.json()
                        print(f"   📄 {data.get('message', 'Mock PDF')}")
                    else:
                        print(f"   📄 PDF: {len(response.content)} octets")
                elif "audits" in url:
                    try:
                        data = response.json()
                        audits = data.get('audits', [])
                        print(f"   📝 {len(audits)} audits trouvés")
                    except:
                        print(f"   📋 Données reçues")
                else:
                    print(f"   🌐 Page accessible")
                    
            elif response.status_code == 403:
                print(f"   ❌ ACCÈS REFUSÉ (Code: 403)")
                print(f"   Vérifiez que vous êtes admin")
            elif response.status_code == 404:
                print(f"   ❌ PAGE NON TROUVÉE (Code: 404)")
                print(f"   Cette route n'existe pas")
            elif response.status_code == 429:
                print(f"   ⚠️ TROP DE REQUÊTES (Code: 429)")
                print(f"   Attendez 60 secondes")
            else:
                print(f"   ❌ CODE {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ SERVEUR NON DÉMARRÉ")
            print(f"   ❗ Démarrer le serveur: uvicorn main:app --reload")
            break
        except Exception as e:
            print(f"   ❌ ERREUR: {e}")
            
except ImportError:
    print("\n❌ ERREUR: 'requests' n'est pas installé")
    print("📦 Installez-le avec: pip install requests")
    print("\nDans VS Code Terminal, tapez:")
    print("pip install requests")
    print("\nPuis réessayez: python test_dashboard.py")
except Exception as e:
    print(f"\n❌ ERREUR GÉNÉRALE: {e}")

print("\n" + "="*60)
print("🎉 FIN DES TESTS")
print("="*60)

print("\n📊 QUE SIGNIFIENT LES RÉSULTATS:")
print("✅ Tout vert = Votre dashboard fonctionne!")
print("❌ 403 = Vous n'avez pas les droits admin")
print("❌ 404 = La route n'existe pas")
print("❌ Connexion = Serveur non démarré")

print("\n💡 PROCHAINES ÉTAPES:")
print("1. Si tout est ✅: Félicitations!")
print("2. Si ❌: Suivez les instructions ci-dessus")