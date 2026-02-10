from datetime import datetime, timedelta
from typing import Optional
import os

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import get_db
from models.user import User

# ======================
# CONFIG JWT (ENV)
# ======================
SECRET_KEY = os.getenv("SECRET_KEY", "SUPER_SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ======================
# CRÉATION ACCESS TOKEN
# ======================
def create_access_token(user_id: int, role: str, expires_delta: Optional[timedelta] = None) -> str:
    """Crée un JWT access token avec l'ID utilisateur et son rôle"""
    expire = datetime.utcnow() + (
        expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": str(user_id),   # ⚠️ ID utilisateur
        "role": role,          # ⚠️ rôle ajouté
        "exp": expire
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# ======================
# CRÉATION REFRESH TOKEN
# ======================
def create_refresh_token(user_id: int, role: str, expires_delta: Optional[timedelta] = None) -> str:
    """Crée un JWT refresh token avec l'ID utilisateur et son rôle"""
    expire = datetime.utcnow() + (
        expires_delta if expires_delta else timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# ======================
# USER OBLIGATOIRE (API protégée)
# ======================
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Récupère l'utilisateur courant à partir du JWT"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré ❌",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise credentials_exception

    return user

# ======================
# USER OPTIONNEL (pages publiques)
# ======================
def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db)
):
    """Récupère l'utilisateur courant si un token est présent dans les cookies"""
    token = request.cookies.get("access_token")
    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return None
    except JWTError:
        return None

    return db.query(User).filter(User.id == int(user_id)).first()

# ======================
# DÉCODAGE SIMPLE
# ======================
def decode_access_token(token: str) -> Optional[dict]:
    """Décodage brut du JWT pour inspection"""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
