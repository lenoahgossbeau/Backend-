import pytest
import requests
import sys

BASE_URL = "http://localhost:8000"

def test_backend():
    """Test complet du backend FastAPI - Version pytest compatible"""
    print("🔧 TEST DU BACKEND")
    print("=" * 60)

    try:
        # 1. LOGIN
        print("\n1. 🔐 Login...")
        login_data = {"email": "admin@test.com", "password": "admin123"}
        resp = requests.post(f"{BASE_URL}/login", json=login_data, timeout=10)

        # Vérification avec assert
        assert resp.status_code == 200, f"Login échoué - Status: {resp.status_code}"
        
        token = resp.json().get("access_token")
        assert token is not None, "Token manquant dans la réponse"
        
        print(f"✅ Login OK - Token: {token[:30]}...")
        headers = {"Authorization": f"Bearer {token}", "accept": "application/json"}

        # 2. DASHBOARD
        print("\n2. 📊 Dashboard stats...")
        resp = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers, timeout=10)
        
        # Accepte 200 (succès) ou 403 (pas admin) mais pas d'autres erreurs
        assert resp.status_code in [200, 403], f"Dashboard KO - Status: {resp.status_code}"
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ Dashboard OK - Utilisateurs: {data.get('general', {}).get('total_users', 'N/A')}")
        else:
            print("⚠️  Dashboard - Accès refusé (pas admin)")

        # 3. DASHBOARD CHARTS
        print("\n3. 📈 Dashboard charts...")
        resp = requests.get(f"{BASE_URL}/api/dashboard/charts", headers=headers, timeout=10)
        assert resp.status_code == 200, f"Charts KO - Status: {resp.status_code}"
        print("✅ Charts OK")

        # 4. PDF
        print("\n4. 📄 PDF test...")
        resp = requests.get(f"{BASE_URL}/api/pdf/test", headers=headers, timeout=10)
        assert resp.status_code == 200, f"PDF KO - Status: {resp.status_code}"
        
        # Sauvegarde conditionnelle seulement si test réussi
        pdf_content = resp.content
        assert len(pdf_content) > 0, "PDF vide"
        
        with open("test_backend_output.pdf", "wb") as f:
            f.write(pdf_content)
        print(f"✅ PDF généré - Taille: {len(pdf_content)} bytes")

        # 5. HEALTH
        print("\n5. ❤️ Health check...")
        resp = requests.get(f"{BASE_URL}/health", timeout=10)
        assert resp.status_code == 200, f"Health KO - Status: {resp.status_code}"
        
        data = resp.json()
        assert data.get('status') == 'healthy', f"Health status incorrect: {data.get('status')}"
        print(f"✅ Health OK - Status: {data.get('status', 'N/A')}, DB: {data.get('database', 'N/A')}")

        # 6. INFO
        print("\n6. ℹ️ API info...")
        resp = requests.get(f"{BASE_URL}/api/info", timeout=10)
        assert resp.status_code == 200, f"API info KO - Status: {resp.status_code}"
        print("✅ API info OK")

        print("\n" + "=" * 60)
        print("🎉 BACKEND COMPLÈTEMENT FONCTIONNEL!")
        print("=" * 60)
        
        # Pas de return, car pytest utilise assert

    except requests.exceptions.ConnectionError:
        pytest.fail("❌ Impossible de se connecter au serveur - Lancez: uvicorn main:app --reload --port 8000")
    except requests.exceptions.Timeout:
        pytest.fail("❌ Timeout - Serveur trop lent à répondre")
    except AssertionError as e:
        pytest.fail(f"❌ Échec du test: {e}")
    except Exception as e:
        pytest.fail(f"❌ Erreur inattendue: {type(e).__name__}: {e}")

if __name__ == "__main__":
    # Pour exécution manuelle
    try:
        # Simuler un test pytest
        test_backend()
        print("\n✅ Tous les tests passent!")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test échoué: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        sys.exit(1)