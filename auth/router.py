from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import resend
import os
import bcrypt
from pydantic import BaseModel  # ✅ AJOUTÉ

from database import get_db
from models.user import User
from models.profile import Profile
from models.audit import Audit
from models.refresh_token import RefreshToken

from auth.schemas import UserCreate, UserLogin, Token
from auth.security import hash_password, verify_password
from auth.jwt import create_access_token, create_refresh_token, decode_access_token, create_activation_token, get_current_user

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

    # Créer l'utilisateur
    user = User(
        email=user_data.email,
        password=hash_password(user_data.password),
        role="researcher",
        status="inactive",
        is_active=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Créer le profil
    profile = Profile(
        user_id=user.id,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        grade="Non spécifié"
    )
    db.add(profile)
    db.commit()

    # Audit
    audit_log = Audit(
        user_id=user.id,
        user_role=user.role,
        action_description="Nouvel utilisateur inscrit"
    )
    db.add(audit_log)
    db.commit()

    # Générer le token JWT d'activation
    activation_token = create_activation_token(user.email)
    activation_link = f"http://localhost:3000/auth/activate?token={activation_token}"
    print(f"\n🔗 LIEN D'ACTIVATION JWT : {activation_link}\n")

    # Envoi de l'email d'activation via Resend
    resend.api_key = os.getenv("RESEND_API_KEY")
    try:
        resend.Emails.send(
            {
                "from": "Activation <onboarding@resend.dev>",
                "to": [user.email],
                "subject": "Active ton compte chercheur",
                "html": f"""
                <h2>Bienvenue sur InchTechs</h2>
                <p>Clique sur le lien ci-dessous pour activer ton compte :</p>
                <a href="{activation_link}">{activation_link}</a>
                <p>Ce lien expire dans 24h.</p>
                """
            }
        )
        print(f"✅ Email d'activation envoyé à {user.email}")
    except Exception as e:
        print(f"❌ Erreur envoi email : {e}")

    # Créer les tokens de session
    access_token = create_access_token(
        user_id=user.id,
        role=user.role,
        expires_delta=timedelta(minutes=15)
    )
    refresh_token = create_refresh_token(
        user_id=user.id,
        role=user.role,
        expires_delta=timedelta(days=7)
    )

    # Stocker refresh token
    db_refresh = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        revoked=False
    )
    db.add(db_refresh)
    db.commit()

    response = JSONResponse({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    })
    response.set_cookie("access_token", access_token, httponly=True, secure=False, samesite="lax")
    response.set_cookie("refresh_token", refresh_token, httponly=True, secure=False, samesite="lax")
    return response


# ======================
# LOGIN
# ======================
@router.post("/login", response_model=Token)
def login(user_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()

    if not user or not verify_password(user_data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants incorrects")

    if user.status != "active":
        raise HTTPException(status_code=403, detail="Compte désactivé")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Compte non activé. Vérifiez vos emails.")

    # Créer les tokens
    access_token = create_access_token(
        user_id=user.id,
        role=user.role,
        expires_delta=timedelta(minutes=15)
    )
    refresh_token = create_refresh_token(
        user_id=user.id,
        role=user.role,
        expires_delta=timedelta(days=7)
    )

    # Audit
    audit_log = Audit(
        user_id=user.id,
        user_role=user.role,
        action_description="Connexion réussie"
    )
    db.add(audit_log)

    # Stocker refresh token
    db_refresh = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        revoked=False
    )
    db.add(db_refresh)
    db.commit()

    response = JSONResponse({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role
        }
    })
    response.set_cookie("access_token", access_token, httponly=True, secure=False, samesite="lax")
    response.set_cookie("refresh_token", refresh_token, httponly=True, secure=False, samesite="lax")
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

    db_token = db.query(RefreshToken).filter_by(token=refresh_token, revoked=False).first()
    if not db_token:
        raise HTTPException(status_code=401, detail="Refresh token révoqué ou inexistant")

    if db_token.expires_at and db_token.expires_at < datetime.now(timezone.utc):
        db_token.revoked = True
        db.commit()
        raise HTTPException(status_code=401, detail="Refresh token expiré")

    user = db.query(User).filter(User.id == db_token.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    new_access_token = create_access_token(
        user_id=user.id,
        role=user.role,
        expires_delta=timedelta(minutes=15)
    )

    response = JSONResponse({
        "access_token": new_access_token,
        "token_type": "bearer"
    })
    response.set_cookie("access_token", new_access_token, httponly=True, secure=False, samesite="lax")
    return response


# ======================
# LOGOUT
# ======================
@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    user_id = None
    user_role = "anonymous"
    
    if refresh_token:
        db_token = db.query(RefreshToken).filter_by(token=refresh_token).first()
        if db_token:
            user_id = db_token.user_id
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user_role = user.role
            db_token.revoked = True
            db.commit()

    if user_id is not None:
        audit_log = Audit(
            user_id=user_id,
            user_role=user_role,
            action_description="Déconnexion"
        )
        db.add(audit_log)
        db.commit()

    response = JSONResponse({"message": "Déconnecté ✅"})
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response


# ======================
# CHANGE PASSWORD
# ======================
class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

@router.put("/change-password")
def change_password(
    request: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Vérifier l'ancien mot de passe
    if not verify_password(request.current_password, current_user.password):
        raise HTTPException(status_code=401, detail="Mot de passe actuel incorrect")
    
    # Hacher le nouveau mot de passe
    new_hashed = bcrypt.hashpw(request.new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    current_user.password = new_hashed
    db.commit()
    
    return {"message": "Mot de passe mis à jour avec succès"}