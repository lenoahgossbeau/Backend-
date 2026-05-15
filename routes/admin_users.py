from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File, Form
from fastapi.responses import StreamingResponse, HTMLResponse
from sqlalchemy.orm import Session
from io import StringIO
import csv
import json
import os
import shutil
import requests
import bcrypt
from datetime import datetime, timezone

from database import get_db
from models.user import User
from models.audit import Audit
from models.profile import Profile
from auth.jwt import get_current_user, create_activation_token
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

admin_users_router = APIRouter(
    prefix="/admin/users",
    tags=["Admin Users"]
)

templates = Jinja2Templates(directory="templates")

# Schéma pour le changement de rôle
class RoleChangeRequest(BaseModel):
    role: str

# Schéma pour la création d’un utilisateur
class UserCreateRequest(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    role: str = "researcher"

# ======================
# LISTE DES UTILISATEURS (JSON) avec audit
# ======================
@admin_users_router.get("/")
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    role: str = Query(None),
    status: str = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100)
):
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")

    query = db.query(User)

    if role:
        query = query.filter(User.role == role)
    if status:
        query = query.filter(User.status == status)

    total = query.count()
    users = query.offset((page - 1) * per_page).limit(per_page).all()

    audit_log = Audit(
        user_id=current_user.id,
        user_role=current_user.role,
        action_description=f"Consultation utilisateurs (role={role}, status={status}, page={page})",
        date=datetime.now(timezone.utc)
    )
    db.add(audit_log)
    db.commit()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "role": u.role,
                "status": u.status,
                "profile": {
                    "first_name": u.profile.first_name if u.profile else None,
                    "last_name": u.profile.last_name if u.profile else None
                } if u.profile else None
            }
            for u in users
        ]
    }

# ======================
# CRÉATION D’UN UTILISATEUR (par l’admin)
# ======================
@admin_users_router.post("/", status_code=201)
def create_user(
    payload: UserCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")

    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    # Hachage du mot de passe
    hashed = bcrypt.hashpw(payload.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    is_admin_role = payload.role in ["admin", "super_admin"]
    
    new_user = User(
        email=payload.email,
        password=hashed,
        role=payload.role,
        status="active" if is_admin_role else "inactive",
        is_active=is_admin_role
    )
    db.add(new_user)
    db.flush()

    profile = Profile(
        user_id=new_user.id,
        first_name=payload.first_name,
        last_name=payload.last_name
    )
    db.add(profile)
    db.commit()

    if not is_admin_role:
        token = create_activation_token(new_user.email)
        activation_link = f"http://localhost:8000/auth/activate?token={token}"
        print(f"\n🔗 LIEN D'ACTIVATION POUR {new_user.email} :\n{activation_link}\n")
        return {"message": "Chercheur créé avec succès. Un email d'activation lui a été envoyé.", "user_id": new_user.id}
    else:
        print(f"\n✅ Admin {new_user.email} créé et activé directement.\n")
        return {"message": f"Admin {payload.role} créé avec succès (compte actif)", "user_id": new_user.id}

# ======================
# EXPORT CSV avec audit
# ======================
@admin_users_router.get("/export")
def export_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    role: str = Query(None),
    status: str = Query(None)
):
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")

    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if status:
        query = query.filter(User.status == status)

    users = query.all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Email", "Role", "Status", "Prénom", "Nom"])
    for u in users:
        writer.writerow([
            u.id, 
            u.email, 
            u.role, 
            u.status,
            u.profile.first_name if u.profile else "",
            u.profile.last_name if u.profile else ""
        ])

    output.seek(0)

    audit_log = Audit(
        user_id=current_user.id,
        user_role=current_user.role,
        action_description=f"Export CSV utilisateurs (role={role}, status={status})",
        date=datetime.now(timezone.utc)
    )
    db.add(audit_log)
    db.commit()

    return StreamingResponse(output, media_type="text/csv", headers={
        "Content-Disposition": "attachment; filename=users_export.csv"
    })

# ======================
# PAGE HTML
# ======================
@admin_users_router.get("/page", response_class=HTMLResponse)
def users_page(request: Request, current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    return templates.TemplateResponse(request, "users.html")

# ======================
# CHANGER LE RÔLE D'UN UTILISATEUR
# ======================
@admin_users_router.put("/{user_id}/role")
def change_user_role(
    user_id: int,
    payload: RoleChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Seul un super_admin peut changer les rôles")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    new_role = payload.role
    if new_role not in ["researcher", "admin", "super_admin"]:
        raise HTTPException(status_code=400, detail="Rôle invalide")
    
    old_role = user.role
    user.role = new_role
    db.commit()
    
    audit_log = Audit(
        user_id=current_user.id,
        user_role=current_user.role,
        action_description=f"Changement de rôle de {user.email} : {old_role} → {new_role}",
        date=datetime.now(timezone.utc)
    )
    db.add(audit_log)
    db.commit()
    
    return {
        "message": f"Rôle de {user.email} changé avec succès",
        "user_id": user.id,
        "old_role": old_role,
        "new_role": new_role
    }

# ======================
# SUPPRIMER UN UTILISATEUR
# ======================
@admin_users_router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas supprimer votre propre compte")
    
    audit_log = Audit(
        user_id=current_user.id,
        user_role=current_user.role,
        action_description=f"Suppression de l'utilisateur {user.email} (ID: {user.id})",
        date=datetime.now(timezone.utc)
    )
    db.add(audit_log)
    
    db.delete(user)
    db.commit()
    
    return None

# ======================
# IMPORT CONTENU INITIAL (CHERCHEUR)
# ======================
@admin_users_router.post("/{user_id}/import-content")
def import_content(
    user_id: int,
    bio: str = Form(None),
    cv: UploadFile = File(None),
    photo: UploadFile = File(None),
    publications: UploadFile = File(None),
    projects: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    if user.role != "researcher":
        raise HTTPException(status_code=400, detail="Seul un chercheur peut recevoir du contenu initial")
    
    profile = user.profile
    if not profile:
        profile = Profile(user_id=user.id)
        db.add(profile)
    
    # 1. Mettre à jour la bio
    if bio:
        profile.bio = bio
    
    # 2. Sauvegarder le CV (PDF)
    if cv:
        cv_dir = "uploads/cv"
        os.makedirs(cv_dir, exist_ok=True)
        cv_filename = f"{user.id}_{cv.filename}"
        cv_path = os.path.join(cv_dir, cv_filename)
        with open(cv_path, "wb") as buffer:
            shutil.copyfileobj(cv.file, buffer)
        profile.cv_url = f"/{cv_path}"
    
    # 3. Sauvegarder la photo
    if photo:
        photo_dir = "uploads/photos"
        os.makedirs(photo_dir, exist_ok=True)
        photo_filename = f"{user.id}_{photo.filename}"
        photo_path = os.path.join(photo_dir, photo_filename)
        with open(photo_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        profile.avatar = f"/{photo_path}"
    
    # 4. Importer les publications via la route interne
    if publications:
        try:
            data = json.load(publications.file)
            token = create_activation_token(current_user.email)
            for item in data:
                pub_data = {
                    "title": item.get("title", ""),
                    "year": int(item.get("date", "2024")[:4]) if item.get("date") else 2024,
                    "description": item.get("description", ""),
                    "coauthors": item.get("coauthors", [])
                }
                response = requests.post(
                    "http://localhost:8000/publications/",
                    json=pub_data,
                    headers={"Authorization": f"Bearer {token}"}
                )
                if response.status_code != 201:
                    print(f"Erreur import publication: {response.text}")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erreur publication JSON: {e}")
    
    # 5. Importer les projets via la route interne
    if projects:
        try:
            data = json.load(projects.file)
            token = create_activation_token(current_user.email)
            for item in data:
                proj_data = {
                    "title": item.get("title", ""),
                    "year": int(item.get("date", "2024")[:4]) if item.get("date") else 2024,
                    "description": item.get("description", ""),
                    "coauthor": item.get("coauthors", [])
                }
                response = requests.post(
                    "http://localhost:8000/projects/",
                    json=proj_data,
                    headers={"Authorization": f"Bearer {token}"}
                )
                if response.status_code != 201:
                    print(f"Erreur import projet: {response.text}")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Erreur projet JSON: {e}")
    
    db.commit()
    
    return {
        "message": "Contenu importé avec succès",
        "user_id": user.id,
        "bio_updated": bool(bio),
        "cv_uploaded": cv is not None,
        "photo_uploaded": photo is not None
    }