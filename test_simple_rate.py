import sys
import os

# AJOUTEZ CES LIGNES
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from fastapi.testclient import TestClient
from main import app, requests_counter
import time

client = TestClient(app)

def test_simple_rate_limit():
    """Test simple du rate limiter"""
    # Réinitialiser le compteur
    requests_counter.clear()
    
    # Route qui existe et n'a pas besoin d'authentification
    endpoint = "/"
    
    print("Test du rate limiter...")
    
    # Les 100 premières requêtes doivent passer
    successful = 0
    for i in range(105):
        response = client.get(endpoint)
        if response.status_code == 200:
            successful += 1
        elif response.status_code == 429:
            print(f"Bloqué à la requête {i+1}")
            break
    
    print(f"Requêtes réussies: {successful}")
    
    # Vérifier que 100 requêtes ont réussi
    assert successful == 100, f"Seulement {successful} requêtes ont réussi au lieu de 100"
    
    print("✅ Test réussi!")

if __name__ == "__main__":
    test_simple_rate_limit()