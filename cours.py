# routes/cours.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.cours import Cours  # IMPORTANT: import spécifique
from schemas.cours import CoursCreate, CoursRead, CoursUpdate

router = APIRouter(prefix="/cours", tags=["Cours"])

# CREATE
@router.post("/", response_model=CoursRead)
def create_cours(cours: CoursCreate, db: Session = Depends(get_db)):
    # CORRECTION: Remplacez .dict() par .model_dump()
    new_cours = Cours(**cours.model_dump())
    db.add(new_cours)
    db.commit()
    db.refresh(new_cours)
    return new_cours

# READ
@router.get("/", response_model=List[CoursRead])  # CORRECTION: List avec 'L' majuscule
def read_all_cours(db: Session = Depends(get_db)):
    return db.query(Cours).all()

# READ SINGLE
@router.get("/{id}", response_model=CoursRead)
def read_cours(id: int, db: Session = Depends(get_db)):
    # CORRECTION: Utilisez filter().first() au lieu de .get()
    db_cours = db.query(Cours).filter(Cours.id == id).first()
    if not db_cours:
        raise HTTPException(status_code=404, detail="Cours non trouvé")
    return db_cours

# UPDATE
@router.put("/{id}", response_model=CoursRead)
def update_cours(id: int, cours: CoursUpdate, db: Session = Depends(get_db)):
    # CORRECTION: Utilisez filter().first() au lieu de .get()
    db_cours = db.query(Cours).filter(Cours.id == id).first()
    if not db_cours:
        raise HTTPException(status_code=404, detail="Cours non trouvé")
    
    # CORRECTION: Remplacez .dict() par .model_dump()
    update_data = cours.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_cours, key, value)
    
    db.commit()
    db.refresh(db_cours)
    return db_cours

# DELETE
@router.delete("/{id}")
def delete_cours(id: int, db: Session = Depends(get_db)):
    # CORRECTION: Utilisez filter().first() au lieu de .get()
    db_cours = db.query(Cours).filter(Cours.id == id).first()
    if not db_cours:
        raise HTTPException(status_code=404, detail="Cours non trouvé")
    
    db.delete(db_cours)
    db.commit()
    return {"message": "Cours supprimé"}