from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas.user import UserCreate, UserOut
from models.user import User
from models.audit import Audit
from database import get_db
from auth.dependencies import get_current_admin
import bcrypt

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

# ================== INSCRIPTION ==================
@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(
        (User.email == user.email) 
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email ou username déjà utilisé ❌")

    hashed_pw = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    new_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_pw,
        role=user.role or "user",
        status=user.status or "active"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    audit_log = Audit(
        user_id=new_user.id,
        user_role=new_user.role,
        action_description=f"Nouvel utilisateur créé: {new_user.username}"
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
