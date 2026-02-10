# manual_test_fastapi.py
import requests
import json
import sys
import os
import re  # Ajouté pour nettoyer les noms de fichiers

BASE_URL = "http://localhost:8000"

def print_response(label, response):
    print(f"\n{'='*60}")
    print(f"🔍 {label}")
    print(f"{'='*60}")
    print(f"📊 Status: {response.status_code}")
    
    # Afficher les headers importants
    headers = dict(response.headers)
    print(f"📦 Content-Type: {headers.get('content-type', 'N/A')}")
    print(f"📏 Content-Length: {headers.get('content-length', 'N/A')}")
    
    try:
        content_type = headers.get('content-type', '').lower()
        
        if 'application/json' in content_type:
            data = response.json()
            print(f"📄 Response Body:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
        elif 'application/pdf' in content_type:
            print(f"📄 PDF reçu: {len(response.content)} bytes")
            # CORRECTION : Nettoyer le nom du fichier
            filename = f"test_output_{label}.pdf"
            # Remplacer les caractères problématiques
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            filename = filename.replace(' ', '_').replace('(', '').replace(')', '')
            
            try:
                with open(filename, "wb") as f:
                    f.write(response.content)
                print(f"💾 PDF sauvegardé: {filename}")
            except Exception as save_error:
                print(f"⚠️  Erreur sauvegarde PDF: {save_error}")
                # Sauvegarde d'urgence avec nom simple
                simple_name = "test_output.pdf"
                with open(simple_name, "wb") as f:
                    f.write(response.content)
                print(f"💾 PDF sauvegardé (nom simple): {simple_name}")
                
        elif 'text/csv' in content_type or 'text/comma-separated-values' in content_type:
            print(f"📄 CSV reçu: {len(response.content)} bytes")
            # Sauvegarder le CSV
            filename = f"test_output_{label}.csv"
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            filename = filename.replace(' ', '_').replace('(', '').replace(')', '')
            
            try:
                with open(filename, "wb") as f:
                    f.write(response.content)
                print(f"💾 CSV sauvegardé: {filename}")
            except Exception as save_error:
                print(f"⚠️  Erreur sauvegarde CSV: {save_error}")
                
        else:
            preview = response.text[:300] if response.text else "No content"
            print(f"📄 Preview: {preview}...")
            
    except json.JSONDecodeError:
        print(f"❌ Erreur JSON invalide")
        print(f"📄 Raw: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ Erreur parsing response: {e}")
        print(f"📄 Raw preview: {response.text[:200] if response.text else 'No text'}...")

def test_login():
    """Test de connexion - UTILISE /login (sans /auth)"""
    print("\n" + "="*60)
    print("1️⃣  TEST LOGIN avec /login")
    print("="*60)
    
    login_data = {
        "email": "admin@test.com",
        "password": "admin123"
    }
    
    response = requests.post(
        f"{BASE_URL}/login",
        json=login_data,
        headers={"Content-Type": "application/json", "accept": "application/json"}
    )
    
    print_response("POST /login", response)
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        if token:
            print(f"\n✅ Token obtenu: {token[:50]}...")
            return token
        else:
            print("❌ Token non trouvé dans la réponse")
            return None
    else:
        print("❌ Échec de la connexion avec /login")
        return None

def test_dashboard(token):
    """Test des endpoints dashboard"""
    print("\n" + "="*60)
    print("2️⃣  TEST DASHBOARD ENDPOINTS")
    print("="*60)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "accept": "application/json"
    }
    
    # Test stats
    print("\n📈 Test /api/dashboard/stats")
    response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
    print_response("GET /api/dashboard/stats", response)
    
    # Test charts
    print("\n📊 Test /api/dashboard/charts")
    response = requests.get(f"{BASE_URL}/api/dashboard/charts?days=7", headers=headers)
    print_response("GET /api/dashboard/charts", response)
    
    # Test activities
    print("\n🔄 Test /api/dashboard/recent-activities")
    response = requests.get(f"{BASE_URL}/api/dashboard/recent-activities?limit=5", headers=headers)
    print_response("GET /api/dashboard/recent-activities", response)

def test_pdf(token):
    """Test des endpoints PDF"""
    print("\n" + "="*60)
    print("3️⃣  TEST PDF ENDPOINTS")
    print("="*60)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "accept": "application/pdf,application/json"
    }
    
    # Test PDF simple
    print("\n📄 Test /api/pdf/test (PDF simple)")
    response = requests.get(f"{BASE_URL}/api/pdf/test", headers=headers)
    print_response("GET /api/pdf/test", response)
    
    # Test génération PDF avec données
    print("\n📄 Test /api/pdf/generate (PDF dashboard)")
    
    pdf_request = {
        "title": "Rapport Dashboard",
        "content": "Rapport complet des statistiques",
        "data_type": "dashboard",
        "filters": {}
    }
    
    response = requests.post(
        f"{BASE_URL}/api/pdf/generate",
        json=pdf_request,
        headers={**headers, "Content-Type": "application/json"}
    )
    
    print_response("POST /api/pdf/generate dashboard", response)  # Nom simplifié
    
    # Test PDF audits
    print("\n📄 Test /api/pdf/generate (PDF audits)")
    
    pdf_request = {
        "title": "Rapport Audits",
        "content": "Journal des audits récents",
        "data_type": "audits",
        "filters": {"limit": 20}
    }
    
    response = requests.post(
        f"{BASE_URL}/api/pdf/generate",
        json=pdf_request,
        headers={**headers, "Content-Type": "application/json"}
    )
    
    print_response("POST /api/pdf/generate audits", response)  # Nom simplifié

def test_existing_endpoints(token):
    """Test des endpoints existants dans main.py"""
    print("\n" + "="*60)
    print("4️⃣  TEST ENDPOINTS EXISTANTS")
    print("="*60)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "accept": "application/json"
    }
    
    # Test export CSV
    print("\n📊 Test /admin/dashboard/export/csv")
    response = requests.get(f"{BASE_URL}/admin/dashboard/export/csv", headers=headers)
    print_response("GET /admin/dashboard/export/csv", response)
    
    # Test audit stats
    print("\n📈 Test /admin/audit-stats")
    response = requests.get(f"{BASE_URL}/admin/audit-stats?days=7", headers=headers)
    print_response("GET /admin/audit-stats", response)

def test_health():
    """Test des endpoints santé"""
    print("\n" + "="*60)
    print("5️⃣  TEST HEALTH & INFO")
    print("="*60)
    
    # Test health
    print("\n❤️  Test /health")
    response = requests.get(f"{BASE_URL}/health")
    print_response("GET /health", response)
    
    # Test API info
    print("\nℹ️  Test /api/info")
    response = requests.get(f"{BASE_URL}/api/info")
    print_response("GET /api/info", response)

def main():
    """Fonction principale de test"""
    print("🚀 DÉBUT DES TESTS BACKEND FASTAPI")
    print("="*60)
    
    # 1. Test connexion
    token = test_login()
    if not token:
        print("❌ Impossible de continuer sans token")
        print("\n💡 Créez un utilisateur admin d'abord avec:")
        print("python create_admin.py")
        return
    
    # 2. Test dashboard
    test_dashboard(token)
    
    # 3. Test PDF
    test_pdf(token)
    
    # 4. Test endpoints existants
    test_existing_endpoints(token)
    
    # 5. Test santé
    test_health()
    
    print("\n" + "="*60)
    print("✅ TESTS TERMINÉS!")
    print("="*60)

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print(f"❌ Impossible de se connecter à {BASE_URL}")
        print("Vérifiez que le serveur FastAPI est lancé:")
        print("  uvicorn main:app --reload --port 8000")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrompus par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)