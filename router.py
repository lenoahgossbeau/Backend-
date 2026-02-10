from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from database import get_db
from models.user import User
from models.profile import Profile
from models.audit import Audit
from models.refresh_token import RefreshToken  # ✅ ajout

from auth.schemas import UserCreate, UserLogin, Token
from auth.security import hash_password, verify_password
from auth.jwt import create_access_token, decode_access_token

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# ======================
# REGISTER
# ======================
@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, request: Request, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hash_password(user_data.password),
        role="researcher",
        status="active"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    profile = Profile(
        user_id=user.id,
        first_name=user_data.first_name,
        last_name=user_data.last_name
    )
    db.add(profile)
    db.commit()

    audit_log = Audit(
        user_id=user.id,
        user_role=user.role,
        action_description="Nouvel utilisateur inscrit",
        ip=request.client.host,
        date=datetime.utcnow()
    )
    db.add(audit_log)
    db.commit()

    # Générer tokens
    access_token = create_access_token(
        {"sub": str(user.id), "username": user.username, "role": user.role},
        expires_delta=timedelta(minutes=15)
    )
    refresh_token = create_access_token(
        {"sub": str(user.id), "username": user.username, "role": user.role},
        expires_delta=timedelta(days=7)
    )

    # Stocker refresh token en base
    db_refresh = RefreshToken(user_id=user.id, token=refresh_token)
    db.add(db_refresh)
    db.commit()

    response = JSONResponse({"access_token": access_token, "token_type": "bearer"})
    response.set_cookie("access_token", access_token, httponly=True, secure=True, samesite="Strict")
    response.set_cookie("refresh_token", refresh_token, httponly=True, secure=True, samesite="Strict")
    return response


# ======================
# LOGIN
# ======================
@router.post("/login", response_model=Token)
def login(user_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()

    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants incorrects")

    if user.status != "active":
        raise HTTPException(status_code=403, detail="Compte désactivé")

    access_token = create_access_token(
        {"sub": str(user.id), "username": user.username, "role": user.role},
        expires_delta=timedelta(minutes=15)
    )
    refresh_token = create_access_token(
        {"sub": str(user.id), "username": user.username, "role": user.role},
        expires_delta=timedelta(days=7)
    )

    audit_log = Audit(
        user_id=user.id,
        user_role=user.role,
        action_description="Connexion réussie",
        ip=request.client.host,
        date=datetime.utcnow()
    )
    db.add(audit_log)
    db.commit()

    # Stocker refresh token en base
    db_refresh = RefreshToken(user_id=user.id, token=refresh_token)
    db.add(db_refresh)
    db.commit()

    response = JSONResponse({"access_token": access_token, "token_type": "bearer"})
    response.set_cookie("access_token", access_token, httponly=True, secure=True, samesite="Strict")
    response.set_cookie("refresh_token", refresh_token, httponly=True, secure=True, samesite="Strict")
    return response


# ======================
# REFRESH
# ======================
@router.post("/refresh")
def refresh_token(request: Request, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token manquant")

    payload = decode_access_token(refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Refresh token invalide ou expiré")

    # Vérifier en base si non révoqué
    db_token = db.query(RefreshToken).filter_by(token=refresh_token, revoked=False).first()
    if not db_token:
        raise HTTPException(status_code=401, detail="Refresh token révoqué ou inexistant")

    user = db.query(User).filter(User.id == int(payload.get("sub"))).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    new_access_token = create_access_token(
        {"sub": str(user.id), "username": user.username, "role": user.role},
        expires_delta=timedelta(minutes=15)
    )

    response = JSONResponse({"access_token": new_access_token, "token_type": "bearer"})
    response.set_cookie("access_token", new_access_token, httponly=True, secure=True, samesite="Strict")
    return response


# ======================
# LOGOUT
# ======================
@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        db_token = db.query(RefreshToken).filter_by(token=refresh_token).first()
        if db_token:
            db_token.revoked = True
            db.commit()

    audit_log = Audit(
        user_id=None,
        user_role="anonymous",
        action_description="Déconnexion",
        ip=request.client.host,
        date=datetime.utcnow()
    )
    db.add(audit_log)
    db.commit()

    response = JSONResponse({"message": "Déconnecté ✅"})
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response
