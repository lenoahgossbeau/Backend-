from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError

from database import get_db
from models.user import User
from auth.jwt import decode_access_token
from models.audit import Audit

# ================== AUTH SCHEMA ==================
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ================== UTILISATEUR COURANT ==================
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
        payload = decode_access_token(token)
        if payload is None:
            raise credentials_exception

        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        user = db.query(User).filter(User.id == int(user_id)).first()
        if user is None:
            raise credentials_exception

        return user

    except JWTError:
        raise credentials_exception

# ================== ADMIN ONLY ==================
def get_current_admin(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """Vérifie que l'utilisateur est admin, sinon log l'incident et refuse l'accès"""
    if current_user.role != "admin":
        audit_log = Audit(
            user_id=current_user.id,
            user_role=current_user.role,
            action_description="Tentative d'accès non autorisé à une route admin"
        )
        db.add(audit_log)
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès interdit ❌",
        )
    return current_user

# ================== USER ONLY ==================
def get_current_normal_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """Vérifie que l'utilisateur est un simple user"""
    if current_user.role != "user":
        audit_log = Audit(
            user_id=current_user.id,
            user_role=current_user.role,
            action_description="Tentative d'accès non autorisé à une route utilisateur"
        )
        db.add(audit_log)
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux utilisateurs ❌",
        )
    return current_user
