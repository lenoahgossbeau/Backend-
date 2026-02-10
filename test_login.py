import requests

BASE_URL = "http://localhost:8000"

print("Test login seul...")
resp = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "admin@test.com", 
    "password": "admin123"
})

print(f"Status: {resp.status_code}")
print(f"Response: {resp.text}")

if resp.status_code == 200:
    print("✅ Login réussi!")
    token = resp.json().get("access_token")
    print(f"Token: {token[:50]}...")
else:
    print("❌ Login échoué")