# schemas/publication.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class PublicationBase(BaseModel):
    year: int = Field(..., ge=1900, le=2100, description="Année de publication")
    title: str = Field(..., min_length=1, max_length=500, description="Titre de la publication")
    coauthor: List[str] = Field(default_factory=list, description="Liste des coauteurs")
    
    # Optionnels
    journal: Optional[str] = Field(None, max_length=300, description="Journal/conférence")
    doi: Optional[str] = Field(None, max_length=100, description="DOI de la publication")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "year": 2024,
                "title": "Machine Learning for Scientific Discovery",
                "coauthor": ["Alice Smith", "Bob Johnson"],
                "journal": "Nature",
                "doi": "10.1038/s41586-024-07501-3"
            }
        }
    )

class PublicationCreate(PublicationBase):
    profile_id: int = Field(..., description="ID du profil associé")

class PublicationUpdate(BaseModel):
    year: Optional[int] = Field(None, ge=1900, le=2100)
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    coauthor: Optional[List[str]] = None
    journal: Optional[str] = None
    doi: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class PublicationOut(PublicationBase):
    id: int
    profile_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)