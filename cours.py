# schemas/cours.py
from pydantic import BaseModel, ConfigDict
from typing import Optional

class CoursBase(BaseModel):
    profile_id: int
    title: str
    description: Optional[str] = None
    curricula: Optional[str] = None
    
    # CORRECTION: Ajoutez model_config à la classe de base
    model_config = ConfigDict(from_attributes=True)

class CoursCreate(CoursBase):
    pass  # Hérite automatiquement de model_config

class CoursUpdate(CoursBase):
    pass  # Hérite automatiquement de model_config

class CoursRead(CoursBase):
    id: int
    # Pas besoin de redéfinir model_config, hérité de CoursBase