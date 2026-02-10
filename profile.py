# schemas/profile.py
from pydantic import BaseModel, ConfigDict
from typing import Optional

class ProfileBase(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[str] = None
    grade: Optional[str] = None
    specialite: Optional[str] = None
    diplome: Optional[str] = None
    description: Optional[str] = None

class ProfileCreate(ProfileBase):
    pass  # user_id injecté automatiquement via current_user

class ProfileUpdate(ProfileBase):
    pass  # utilisé pour update avec exclude_unset=True

class ProfileOut(ProfileBase):
    id: int
    user_id: int
    
    # ✅ Syntaxe Pydantic v2
    model_config = ConfigDict(from_attributes=True)