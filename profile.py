from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas.profile import ProfileCreate, ProfileOut, ProfileUpdate
from models.profile import Profile
from models.audit import Audit
from database import get_db
from auth.dependencies import get_current_user
from models.user import User

router = APIRouter(
    prefix="/profiles",
    tags=["Profiles"]
)

# ================== CRÉER MON PROFIL ==================
@router.post("/", response_model=ProfileOut)
def create_profile(profile: ProfileCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_profile = Profile(
        **profile.dict(exclude={"user_id"}),  # user_id injecté automatiquement
        user_id=current_user.id
    )
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)

    audit_log = Audit(
        user_id=current_user.id,
        user_role=current_user.role,
        action_description="Profil créé"
    )
    db.add(audit_log)
    db.commit()

    return new_profile

# ================== LIRE UN PROFIL ==================
@router.get("/{profile_id}", response_model=ProfileOut)
def get_profile(
    profile_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
    ):

    profile = (
        db.query(Profile)
        .filter(
            Profile.id == profile_id,
            Profile.user_id == current_user.id
        )
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Profil non trouvé ❌"
        )

    return profile

# ================== METTRE À JOUR MON PROFIL ==================
@router.put("/me", response_model=ProfileOut)
def update_my_profile(data: ProfileUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profil introuvable ❌")
    for key, value in data.dict(exclude_unset=True).items():
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)

    audit_log = Audit(
        user_id=current_user.id,
        user_role=current_user.role,
        action_description="Profil mis à jour"
    )
    db.add(audit_log)
    db.commit()

    return profile

# ================== SUPPRIMER MON PROFIL ==================
@router.delete("/me")
def delete_my_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profil introuvable ❌")
    db.delete(profile)
    db.commit()

    audit_log = Audit(
        user_id=current_user.id,
        user_role=current_user.role,
        action_description="Profil supprimé"
    )
    db.add(audit_log)
    db.commit()

    return {"message": "Profil supprimé ✅"}
