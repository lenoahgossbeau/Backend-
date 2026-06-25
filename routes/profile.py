from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from models.profile import Profile
from models.audit import Audit
from database import get_db
from auth.dependencies import get_current_user
from models.user import User
import os
import shutil
from datetime import datetime

router = APIRouter(
    prefix="/profiles",
    tags=["Profiles"]
)

# ===================== DOSSIER D'UPLOAD PHOTO =====================
PHOTO_UPLOAD_DIR = "uploads/photos"
os.makedirs(PHOTO_UPLOAD_DIR, exist_ok=True)

# Schémas locaux (pour éviter les erreurs d'import)
class ProfileOut(BaseModel):
    id: int
    user_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    grade: Optional[str] = None
    bio: Optional[str] = None
    avatar: Optional[str] = None
    email: Optional[str] = None
    linkedin: Optional[str] = None
    whatsapp: Optional[str] = None
    twitter: Optional[str] = None
    github: Optional[str] = None

class ProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    grade: Optional[str] = None
    bio: Optional[str] = None
    avatar: Optional[str] = None
    email: Optional[str] = None
    linkedin: Optional[str] = None
    whatsapp: Optional[str] = None
    twitter: Optional[str] = None
    github: Optional[str] = None

class ProfileCreate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    grade: Optional[str] = None
    bio: Optional[str] = None
    avatar: Optional[str] = None
    email: Optional[str] = None
    linkedin: Optional[str] = None
    whatsapp: Optional[str] = None
    twitter: Optional[str] = None
    github: Optional[str] = None

# ================== UPLOAD PHOTO ==================
@router.post("/upload-photo")
def upload_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Télécharge une photo pour le chercheur connecté"""
    # Vérifier que c'est une image
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Seuls les fichiers image sont acceptés")
    
    # Vérifier la taille (max 2MB)
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    if size > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="L'image ne doit pas dépasser 2MB")
    
    # Générer un nom de fichier unique
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    extension = file.filename.split('.')[-1]
    filename = f"photo_{current_user.id}_{timestamp}.{extension}"
    filepath = os.path.join(PHOTO_UPLOAD_DIR, filename)
    
    # Sauvegarder le fichier
    try:
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'upload: {str(e)}")
    
    # Mettre à jour le profil avec le chemin de la photo
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profil non trouvé")
    
    profile.profile_picture = f"/uploads/photos/{filename}"
    db.commit()
    
    return {
        "success": True,
        "message": "Photo téléchargée avec succès",
        "photo_url": profile.profile_picture
    }

# ================== CRÉER MON PROFIL ==================
@router.post("/", response_model=ProfileOut)
def create_profile(profile: ProfileCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Vérifier si le profil existe déjà
    existing = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Profil déjà existant")
    
    new_profile = Profile(
        user_id=current_user.id,
        first_name=profile.first_name,
        last_name=profile.last_name,
        grade=profile.grade,
        description=profile.bio,
        profile_picture=profile.avatar,
        email=profile.email,
        linkedin=profile.linkedin,
        whatsapp=profile.whatsapp,
        twitter=profile.twitter,
        github=profile.github
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

    return {
        "id": new_profile.id,
        "user_id": new_profile.user_id,
        "first_name": new_profile.first_name,
        "last_name": new_profile.last_name,
        "grade": new_profile.grade,
        "bio": new_profile.description,
        "avatar": new_profile.profile_picture,
        "email": new_profile.email,
        "linkedin": new_profile.linkedin,
        "whatsapp": new_profile.whatsapp,
        "twitter": new_profile.twitter,
        "github": new_profile.github
    }

# ================== LIRE MON PROFIL (ME) ==================
@router.get("/me", response_model=ProfileOut)
def get_my_profile(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Récupère le profil de l'utilisateur connecté"""
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Profil non trouvé ❌"
        )
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "first_name": profile.first_name,
        "last_name": profile.last_name,
        "grade": profile.grade,
        "bio": profile.description,
        "avatar": profile.profile_picture,
        "email": profile.email,
        "linkedin": profile.linkedin,
        "whatsapp": profile.whatsapp,
        "twitter": profile.twitter,
        "github": profile.github
    }

# ================== LIRE UN PROFIL PAR ID ==================
@router.get("/{profile_id}", response_model=ProfileOut)
def get_profile(
    profile_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    profile = db.query(Profile).filter(
        Profile.id == profile_id,
        Profile.user_id == current_user.id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Profil non trouvé ❌"
        )
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "first_name": profile.first_name,
        "last_name": profile.last_name,
        "grade": profile.grade,
        "bio": profile.description,
        "avatar": profile.profile_picture,
        "email": profile.email,
        "linkedin": profile.linkedin,
        "whatsapp": profile.whatsapp,
        "twitter": profile.twitter,
        "github": profile.github
    }

# ================== METTRE À JOUR MON PROFIL ==================
@router.put("/me", response_model=ProfileOut)
def update_my_profile(
    data: ProfileUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profil introuvable ❌")
    
    if data.first_name is not None:
        profile.first_name = data.first_name
    if data.last_name is not None:
        profile.last_name = data.last_name
    if data.grade is not None:
        profile.grade = data.grade
    if data.bio is not None:
        profile.description = data.bio
    if data.avatar is not None:
        profile.profile_picture = data.avatar
    if data.email is not None:
        profile.email = data.email
    if data.linkedin is not None:
        profile.linkedin = data.linkedin
    if data.whatsapp is not None:
        profile.whatsapp = data.whatsapp
    if data.twitter is not None:
        profile.twitter = data.twitter
    if data.github is not None:
        profile.github = data.github
    
    db.commit()
    db.refresh(profile)

    audit_log = Audit(
        user_id=current_user.id,
        user_role=current_user.role,
        action_description="Profil mis à jour"
    )
    db.add(audit_log)
    db.commit()

    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "first_name": profile.first_name,
        "last_name": profile.last_name,
        "grade": profile.grade,
        "bio": profile.description,
        "avatar": profile.profile_picture,
        "email": profile.email,
        "linkedin": profile.linkedin,
        "whatsapp": profile.whatsapp,
        "twitter": profile.twitter,
        "github": profile.github
    }

# ================== SUPPRIMER MON PROFIL ==================
@router.delete("/me")
def delete_my_profile(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
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

