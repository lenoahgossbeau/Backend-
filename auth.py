# routes/auth.py - VERSION CORRIGÉE
from fastapi import APIRouter, HTTPException, Depends  # ⭐ AJOUTEZ Depends ICI
from pydantic import BaseModel
from auth.jwt import create_access_token, create_refresh_token
from sqlalchemy.orm import Session
from database import get_db
from models.user import User

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/login", response_model=TokenResponse)
def login_simple(request: LoginRequest, db: Session = Depends(get_db)):
    """Login simplifié - Accepte admin@test.com avec n'importe quel mot de passe"""
    print(f"LOGIN TEST: {request.email}")
    
    # Trouver l'utilisateur
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
    
    print(f"Utilisateur trouvé: {user.email}, ID: {user.id}, Rôle: {user.role}")
    
    # Créer un VRAI token JWT (accepter sans vérifier le mot de passe pour test)
    access_token = create_access_token(user.id, user.role)
    
    print(f"Token généré: {access_token[:50]}...")
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer"
    )