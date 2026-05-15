from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.profile import Profile
from models.publication import Publication
from models.project import Project

router = APIRouter(prefix="/researcher/public", tags=["Public Researcher"])

# ====================== LISTE DES CHERCHEURS POUR PAGE D'ACCUEIL ======================
@router.get("/list")
def get_all_public_researchers(db: Session = Depends(get_db)):
    """Récupère tous les chercheurs actifs pour la page d'accueil"""
    researchers = db.query(User).filter(
        User.role == "researcher",
        User.status == "active"
    ).all()  # ✅ Plus de limite, tous les chercheurs actifs sont affichés
    
    result = []
    for r in researchers:
        # Récupère le profil associé
        profile = db.query(Profile).filter(Profile.user_id == r.id).first()
        
        # Construit le nom à partir du profil ou de l'email
        name = r.email.split('@')[0]  # nom par défaut
        if profile:
            if profile.first_name or profile.last_name:
                name = f"{profile.first_name or ''} {profile.last_name or ''}".strip()
        
        result.append({
            "id": r.id,
            "name": name if name else "Chercheur",
            "slug": r.slug,
            "bio": profile.bio if profile and profile.bio else "",
            "photo_url": profile.profile_picture if profile else None,
            "profession": profile.grade if profile and profile.grade else "Chercheur"
        })
    
    return result

# ====================== ROUTE PAR SLUG ======================
@router.get("/slug/{slug}")
def get_public_researcher_by_slug(slug: str, db: Session = Depends(get_db)):
    """Récupère un chercheur par son slug (URL personnalisée)"""
    user = db.query(User).filter(
        User.slug == slug,
        User.role == "researcher",
        User.status == "active"
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="Chercheur non trouvé")

    profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    publications = db.query(Publication).filter(Publication.profile_id == profile.id).all() if profile else []
    projects = db.query(Project).filter(Project.profile_id == profile.id).all() if profile else []

    # Construction du nom
    name = user.email.split('@')[0]
    if profile:
        if profile.first_name or profile.last_name:
            name = f"{profile.first_name or ''} {profile.last_name or ''}".strip()

    return {
        "id": user.id,
        "email": user.email,
        "slug": user.slug,
        "name": name,
        "firstName": profile.first_name if profile else "",
        "lastName": profile.last_name if profile else "",
        "profession": profile.grade if profile else "",
        "bio": profile.bio if profile else "",
        "cvUrl": profile.cv_url if profile else "",
        "avatar": profile.profile_picture if profile else "",
        "publications": [
            {
                "id": pub.id,
                "title": pub.title,
                "year": pub.year,
                "description": getattr(pub, "description", ""),
                "link": getattr(pub, "link", "")
            }
            for pub in publications
        ],
        "projects": [
            {
                "id": proj.id,
                "title": proj.title,
                "year": proj.year,
                "description": proj.description if proj.description else "",
                "link": getattr(proj, "link", "")
            }
            for proj in projects
        ]
    }

# ====================== ROUTE PAR ID ======================
@router.get("/id/{user_id}")
def get_public_researcher_by_id(user_id: int, db: Session = Depends(get_db)):
    """Récupère un chercheur par son ID"""
    user = db.query(User).filter(
        User.id == user_id,
        User.role == "researcher",
        User.status == "active"
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="Chercheur non trouvé")

    profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    publications = db.query(Publication).filter(Publication.profile_id == profile.id).all() if profile else []
    projects = db.query(Project).filter(Project.profile_id == profile.id).all() if profile else []

    # Construction du nom
    name = user.email.split('@')[0]
    if profile:
        if profile.first_name or profile.last_name:
            name = f"{profile.first_name or ''} {profile.last_name or ''}".strip()

    return {
        "id": user.id,
        "email": user.email,
        "slug": user.slug,
        "name": name,
        "firstName": profile.first_name if profile else "",
        "lastName": profile.last_name if profile else "",
        "profession": profile.grade if profile else "",
        "bio": profile.bio if profile else "",
        "cvUrl": profile.cv_url if profile else "",
        "avatar": profile.profile_picture if profile else "",
        "publications": [
            {
                "id": pub.id,
                "title": pub.title,
                "year": pub.year,
                "description": getattr(pub, "description", ""),
                "link": getattr(pub, "link", "")
            }
            for pub in publications
        ],
        "projects": [
            {
                "id": proj.id,
                "title": proj.title,
                "year": proj.year,
                "description": proj.description if proj.description else "",
                "link": getattr(proj, "link", "")
            }
            for proj in projects
        ]
    }