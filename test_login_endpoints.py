# test_login_endpoints.py
import requests

BASE_URL = "http://localhost:8000"

print("🔍 TEST DES DIFFÉRENTS ENDPOINTS DE LOGIN")
print("="*60)

# Testez tous les endpoints possibles
endpoints = [
    "/auth/login",      # Si dans auth_router avec préfixe /auth
    "/login",           # Si dans auth_routes_router sans préfixe
    "/api/auth/login",  # Autre possibilité
    "/user/login",      # Peut-être ici
]

login_data = {
    "email": "admin@test.com",
    "password": "admin123"
}

for endpoint in endpoints:
    print(f"\nTest {endpoint}...")
    try:
        response = requests.post(
            f"{BASE_URL}{endpoint}",
            json=login_data,
            timeout=3
        )
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print(f"  ✅ SUCCÈS! Token: {response.json().get('access_token', 'N/A')[:30]}...")
            break
        elif response.status_code != 404:
            print(f"  Réponse: {response.text[:100]}")
    except Exception as e:
        print(f"  ❌ Erreur: {e}")

print("\n" + "="*60)
print("💡 Conseil: Allez sur http://localhost:8000/docs et cherchez")
print("la route de login dans la documentation Swagger.")