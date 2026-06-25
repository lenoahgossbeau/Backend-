# tests/conftest.py - VERSION AVEC SHA256
import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import hashlib
import sys

# Ajouter le chemin du projet au sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base, get_db
from main import app
from fastapi.testclient import TestClient

# ===================== CONFIGURATION ENVIRONNEMENT TEST =====================
os.environ["SECRET_KEY"] = "your-super-secret-key-for-testing-123"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"
os.environ["ENV"] = "test"  # IMPORTANT pour contourner auth en test

# ===================== MOCK DE HASH PASSWORD POUR TESTS =====================
# Import après avoir défini les variables d'environnement
from auth import security

# Sauvegarde de la fonction originale
original_hash_password = security.hash_password
original_verify_password = security.verify_password

def mock_hash_password(password: str) -> str:
    """Mock de hash_password pour tests (SHA256 simple)"""
    # SHA256 simple pour éviter les problèmes bcrypt en test
    return hashlib.sha256(password.encode()).hexdigest()

def mock_verify_password(plain_password: str, hashed_password: str) -> bool:
    """Mock de verify_password pour tests"""
    # SHA256 simple pour éviter les problèmes bcrypt en test
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

# Application du mock
security.hash_password = mock_hash_password
security.verify_password = mock_verify_password

# ===================== DATABASE TEST (en mémoire) =====================
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ===================== FIXTURE DB =====================
@pytest.fixture(scope="function")
def db():
    """Fixture pour créer/supprimer les tables à chaque test"""
    # Créer toutes les tables
    Base.metadata.create_all(bind=engine)
    
    db_session = TestingSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
        # Nettoyer après chaque test
        Base.metadata.drop_all(bind=engine)

# ===================== FIXTURE CLIENT =====================
@pytest.fixture(scope="function")
def client(db):
    """Fixture client avec override de la base de données"""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        # Stocker la db dans l'état de l'app pour y accéder dans les tests
        test_client.app.state.db = db
        yield test_client
    
    # Nettoyer les overrides
    app.dependency_overrides.clear()

# ===================== FIXTURE POUR TOKEN ADMIN =====================
@pytest.fixture
def admin_token(client, db):
    """Fixture pour créer un utilisateur admin et obtenir un token"""
    # Créer un utilisateur admin directement dans la DB
    from models.user import User
    
    admin_user = User(
        email="admin@test.com",
        password=security.hash_password("Admin123!"),  # Utilise le mock SHA256
        role="admin",
        status="active"
    )
    
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    # Créer un token JWT manuellement
    from datetime import datetime, timedelta
    import jwt
    
    secret_key = os.getenv("SECRET_KEY", "your-super-secret-key-for-testing-123")
    algorithm = os.getenv("ALGORITHM", "HS256")
    
    data = {
        "sub": str(admin_user.id),
        "email": admin_user.email,
        "role": admin_user.role,
        "exp": datetime.utcnow() + timedelta(minutes=60)
    }
    
    token = jwt.encode(data, secret_key, algorithm=algorithm)
    
    return token

# ===================== FIXTURE POUR HEADERS ADMIN =====================
@pytest.fixture
def admin_headers(admin_token):
    """Headers avec token d'admin"""
    return {"Authorization": f"Bearer {admin_token}"}

# ===================== NETTOYAGE APRÈS TESTS =====================
@pytest.fixture(scope="session", autouse=True)
def cleanup():
    """Restauration des fonctions originales après tous les tests"""
    yield
    # Restauration des fonctions originales
    security.hash_password = original_hash_password
    security.verify_password = original_verify_password