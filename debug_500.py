# debug_500.py
import requests
import traceback

BASE_URL = "http://localhost:8000"

print("🔧 DEBUG DE L'ERREUR 500 SUR /login")
print("="*60)

login_data = {
    "email": "admin@test.com", 
    "password": "admin123"
}

try:
    print("Envoi de la requête à /login...")
    response = requests.post(f"{BASE_URL}/login", json=login_data, timeout=10)
    
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"\nContenu de la réponse (premieres 500 caractères):")
    print("-"*60)
    print(response.text[:500])
    print("-"*60)
    
except Exception as e:
    print(f"Exception: {e}")
    traceback.print_exc()