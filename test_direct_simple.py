# test_direct_simple.py
import requests
import json

print("TEST DIRECT LE PLUS SIMPLE")
print("-" * 40)

url = "http://localhost:8000/login"
data = {
    "email": "admin@test.com",
    "password": "admin123"
}

print(f"URL: {url}")
print(f"Data: {json.dumps(data)}")

try:
    response = requests.post(url, json=data, timeout=10)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    
    if response.status_code == 500:
        print("\n⚠️  Erreur 500 - Regardez les logs d'uvicorn !")
        print("Dans le terminal où vous avez lancé 'uvicorn main:app --reload'")
        print("Vous devriez voir une erreur détaillée.")
    
    print(f"\nResponse (first 200 chars):")
    print(response.text[:200])
    
except Exception as e:
    print(f"\n❌ Exception: {e}")