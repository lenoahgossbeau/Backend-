from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.profile import Profile
from models.publication import Publication
from models.project import Project
from models.cv import TechnicalSkill, SoftSkill, Language, Degree, Experience

router = APIRouter(prefix="/researcher/public", tags=["Public Researcher"])

# ====================== LISTE DES CHERCHEURS POUR PAGE D'ACCUEIL ======================
@router.get("/list")
def get_all_public_researchers(db: Session = Depends(get_db)):
    """Récupère tous les chercheurs actifs pour la page d'accueil"""
    researchers = db.query(User).filter(
        User.role == "researcher",
        User.status == "active"
    ).all()
    
    result = []
    for r in researchers:
        profile = db.query(Profile).filter(Profile.user_id == r.id).first()
        
        name = r.email.split('@')[0]
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

    # ✅ Récupération des données du CV avec les bonnes classes
    skills_tech = db.query(TechnicalSkill).filter(TechnicalSkill.profile_id == profile.id).all() if profile else []
    skills_soft = db.query(SoftSkill).filter(SoftSkill.profile_id == profile.id).all() if profile else []
    languages = db.query(Language).filter(Language.profile_id == profile.id).all() if profile else []
    degrees = db.query(Degree).filter(Degree.profile_id == profile.id).all() if profile else []
    experiences = db.query(Experience).filter(Experience.profile_id == profile.id).all() if profile else []

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
        ],
        # ✅ AJOUT : Données du CV avec les bonnes classes
        "cv": {
            "skills_tech": [{"name": s.skill_name, "level": s.level} for s in skills_tech],
            "skills_soft": [{"name": s.skill_name} for s in skills_soft],
            "languages": [{"name": l.language, "level": l.level} for l in languages],
            "degrees": [
                {
                    "title": d.title,
                    "institution": d.institution,
                    "year": d.year,
                    "description": d.description
                }
                for d in degrees
            ],
            "experiences": [
                {
                    "title": e.title,
                    "company": e.company,
                    "start_date": e.start_date.isoformat() if e.start_date else None,
                    "end_date": e.end_date.isoformat() if e.end_date else None,
                    "description": e.description
                }
                for e in experiences
            ]
        }
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

    # ✅ Récupération des données du CV avec les bonnes classes
    skills_tech = db.query(TechnicalSkill).filter(TechnicalSkill.profile_id == profile.id).all() if profile else []
    skills_soft = db.query(SoftSkill).filter(SoftSkill.profile_id == profile.id).all() if profile else []
    languages = db.query(Language).filter(Language.profile_id == profile.id).all() if profile else []
    degrees = db.query(Degree).filter(Degree.profile_id == profile.id).all() if profile else []
    experiences = db.query(Experience).filter(Experience.profile_id == profile.id).all() if profile else []

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
        ],
        # ✅ AJOUT : Données du CV avec les bonnes classes
        "cv": {
            "skills_tech": [{"name": s.skill_name, "level": s.level} for s in skills_tech],
            "skills_soft": [{"name": s.skill_name} for s in skills_soft],
            "languages": [{"name": l.language, "level": l.level} for l in languages],
            "degrees": [
                {
                    "title": d.title,
                    "institution": d.institution,
                    "year": d.year,
                    "description": d.description
                }
                for d in degrees
            ],
            "experiences": [
                {
                    "title": e.title,
                    "company": e.company,
                    "start_date": e.start_date.isoformat() if e.start_date else None,
                    "end_date": e.end_date.isoformat() if e.end_date else None,
                    "description": e.description
                }
                for e in experiences
            ]
        }
    }