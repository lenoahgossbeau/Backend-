# routes/project.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models.project import Project
from schemas.project import ProjectCreate, ProjectUpdate, ProjectOut

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.get("/", response_model=List[ProjectOut])
def get_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Récupérer tous les projets"""
    projects = db.query(Project).offset(skip).limit(limit).all()
    return projects

@router.post("/", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """Créer un nouveau projet"""
    db_project = Project(**project.dict())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    """Récupérer un projet par ID"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return project

@router.put("/{project_id}", response_model=ProjectOut)
def update_project(project_id: int, project_update: ProjectUpdate, db: Session = Depends(get_db)):
    """Mettre à jour un projet"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    update_data = project_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    db.commit()
    db.refresh(project)
    return project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """Supprimer un projet"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    db.delete(project)
    db.commit()
    return None