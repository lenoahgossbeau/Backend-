# schemas/project.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class ProjectBase(BaseModel):
    year: int = Field(..., ge=1900, le=2100, description="Année du projet")
    title: str = Field(..., min_length=1, max_length=500, description="Titre du projet")
    coauthor: List[str] = Field(default_factory=list, description="Liste des collaborateurs")
    
    # Optionnels
    description: Optional[str] = Field(None, description="Description détaillée")
    budget: Optional[float] = Field(None, ge=0, description="Budget en euros")
    status: Optional[str] = Field(None, description="Statut (En cours, Terminé, etc.)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "year": 2023,
                "title": "AI for Climate Change Prediction",
                "coauthor": ["Climate Research Lab", "Data Science Team"],
                "description": "Projet sur l'IA pour la prédiction climatique",
                "budget": 150000.00,
                "status": "En cours"
            }
        }
    )

class ProjectCreate(ProjectBase):
    profile_id: int = Field(..., description="ID du profil associé")

class ProjectUpdate(BaseModel):
    year: Optional[int] = Field(None, ge=1900, le=2100)
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    coauthor: Optional[List[str]] = None
    description: Optional[str] = None
    budget: Optional[float] = None
    status: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class ProjectOut(ProjectBase):
    id: int
    profile_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)