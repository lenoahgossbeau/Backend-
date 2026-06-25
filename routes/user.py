from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas.user import UserCreate, UserOut
from models.user import User
from models.profile import Profile
from models.audit import Audit
from database import get_db
from auth.dependencies import get_current_admin
import bcrypt
import re  # ✅ AJOUTÉ pour générer les slugs

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

# ================== FONCTION DE GÉNÉRATION DE SLUG ==================
def generate_slug(email: str) -> str:
    """Génère un slug à partir de l'email"""
    slug = email.split('@')[0].lower()
    slug = re.sub(r'[^a-z0-9-]', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug

# ================== INSCRIPTION ==================
@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email déjà utilisé ❌")

    hashed_pw = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    # Création de l'utilisateur avec slug généré automatiquement
    new_user = User(
        email=user.email,
        password=hashed_pw,
        role=user.role or "researcher",
        status=user.status or "pending",
        slug=generate_slug(user.email)  # ✅ SLUG GÉNÉRÉ AUTOMATIQUEMENT
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Création automatique du profil pour ce chercheur
    new_profile = Profile(
        user_id=new_user.id,
        email=user.email,
        first_name=user.first_name if hasattr(user, 'first_name') else "",
        last_name=user.last_name if hasattr(user, 'last_name') else ""
    )
    db.add(new_profile)
    db.commit()

    audit_log = Audit(
        user_id=new_user.id,
        user_role=new_user.role,
        action_description=f"Nouvel utilisateur créé: {new_user.email}"
    )
    db.add(audit_log)
    db.commit()

    return new_user

# ================== LISTER TOUS LES UTILISATEURS (ADMIN) ==================
@router.get("/", response_model=list[UserOut])
def get_all_users(db: Session = Depends(get_db), current_user = Depends(get_current_admin)):
    return db.query(User).all()

# ================== METTRE À JOUR UN UTILISATEUR (ADMIN) ==================
@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, data: dict, db: Session = Depends(get_db), current_user = Depends(get_current_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable ❌")
    for key, value in data.items():
        if hasattr(user, key):
            setattr(user, key, value)
    db.commit()
    db.refresh(user)

    audit_log = Audit(
        user_id=current_user.id,
        user_role=current_user.role,
        action_description=f"Utilisateur {user.email} mis à jour par admin"
    )
    db.add(audit_log)
    db.commit()

    return user

# ================== SUPPRIMER UN UTILISATEUR (ADMIN) ==================
@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable ❌")
    db.delete(user)
    db.commit()

    audit_log = Audit(
        user_id=current_user.id,
        user_role=current_user.role,
        action_description=f"Utilisateur {user.email} supprimé par admin"
    )
    db.add(audit_log)
    db.commit()

    return {"message": "Utilisateur supprimé ✅"}