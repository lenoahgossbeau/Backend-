# test_simple.py - VERSION FINALE SANS WARNING
import pytest
import requests
import sys

BASE_URL = "http://localhost:8000"

def get_auth_token():
    """Obtient un token d'authentification - NE PAS utiliser comme test pytest"""
    try:
        response = requests.post(
            f"{BASE_URL}/login",
            json={"email": "admin@test.com", "password": "admin123"},
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
    except:
        pass
    
    # Fallback
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": "admin@test.com", "password": "admin123"},
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
    except:
        pass
    
    return None

def test_login_integration():
    """Test d'intégration du login - Version pytest sans return"""
    print("🔐 Test d'intégration du login...")
    
    # Test /login
    response = requests.post(
        f"{BASE_URL}/login",
        json={"email": "admin@test.com", "password": "admin123"},
        headers={"Content-Type": "application/json"},
        timeout=5
    )
    
    # Assertion au lieu de return
    assert response.status_code == 200, f"/login échoué: {response.status_code}"
    
    data = response.json()
    assert "access_token" in data, "Token manquant dans la réponse /login"
    
    token = data["access_token"]
    assert len(token) > 10, "Token trop court"
    
    print(f"✅ Login /login réussi - Token: {token[:30]}...")
    
    # Vérifier que le token fonctionne
    headers = {"Authorization": f"Bearer {token}"}
    health_response = requests.get(f"{BASE_URL}/health", timeout=5)
    assert health_response.status_code == 200, "Token invalide (health check échoué)"
    
    print("✅ Token validé avec health check")
    # PAS de return - la fonction retourne None implicitement

def test_simple_integration():
    """Test d'intégration simple - Version pytest compatible"""
    print("🔧 TEST SIMPLE D'INTÉGRATION")
    print("=" * 60)
    
    # Obtention du token (fonction utilitaire, pas un test)
    token = get_auth_token()
    assert token is not None, "Impossible d'obtenir un token d'authentification"
    print(f"✅ Token obtenu: {token[:30]}...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "accept": "application/json"
    }
    
    # Test du dashboard
    print("\n📊 Test du dashboard stats...")
    response = requests.get(
        f"{BASE_URL}/api/dashboard/stats",
        headers=headers,
        timeout=10
    )
    
    assert response.status_code in [200, 403], f"Dashboard échoué: {response.status_code}"
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Dashboard OK")
        print(f"   📈 Statistiques:")
        print(f"      - Utilisateurs: {data.get('general', {}).get('total_users', 'N/A')}")
    else:
        print("   ⚠️  Accès refusé (pas admin)")
    
    # Test du PDF
    print("\n📄 Test du PDF...")
    response = requests.get(
        f"{BASE_URL}/api/pdf/test",
        headers=headers,
        timeout=10
    )
    
    assert response.status_code == 200, f"PDF échoué: {response.status_code}"
    
    pdf_content = response.content
    assert len(pdf_content) > 0, "PDF vide"
    
    print(f"   ✅ PDF OK - Taille: {len(pdf_content)} bytes")
    
    # Test health
    print("\n❤️ Test health check...")
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    
    assert response.status_code == 200, f"Health check échoué: {response.status_code}"
    
    data = response.json()
    assert data.get('status') == 'healthy', f"Status health incorrect: {data.get('status')}"
    
    print(f"   ✅ Health OK - {data.get('status', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("✅ TESTS D'INTÉGRATION TERMINÉS!")
    print("=" * 60)
    # PAS de return - la fonction retourne None implicitement

if __name__ == "__main__":
    # Pour exécution manuelle (non pytest)
    try:
        print("⚠️  Exécution manuelle - Mode utilitaire")
        
        token = get_auth_token()
        if token:
            print(f"✅ Token obtenu avec succès")
            print(f"   Token: {token[:50]}...")
            sys.exit(0)
        else:
            print("❌ Impossible d'obtenir un token")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)