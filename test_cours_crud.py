import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# Données de test
cours_data = {
    "profile_id": 1,   # ⚠️ Assure-toi qu'un profil avec id=1 existe dans ta BD
    "title": "Développement Web",
    "description": "Cours sur FastAPI et PostgreSQL",
    "curricula": "Backend, API, BD"
}

def test_create_cours():
    response = client.post("/cours/", json=cours_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == cours_data["title"]
    assert "id" in data
    global cours_id
    cours_id = data["id"]

def test_read_cours():
    response = client.get("/cours/")
    assert response.status_code == 200
    data = response.json()
    assert any(c["id"] == cours_id for c in data)

def test_update_cours():
    update_data = cours_data.copy()
    update_data["title"] = "Développement Web Avancé"
    response = client.put(f"/cours/{cours_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Développement Web Avancé"

def test_delete_cours():
    response = client.delete(f"/cours/{cours_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Cours supprimé"

    # Vérifier que le cours n'existe plus
    response = client.get("/cours/")
    data = response.json()
    assert all(c["id"] != cours_id for c in data)
