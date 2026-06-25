# auth/security.py
from passlib.context import CryptContext

# Créer le contexte pour le hachage bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

def hash_password(password: str) -> str:
    """
    Hash un mot de passe en utilisant bcrypt
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Vérifie un mot de passe en clair avec son hash
    """
    return pwd_context.verify(plain_password, hashed_password)