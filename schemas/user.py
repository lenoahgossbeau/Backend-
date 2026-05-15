# schemas/user.py
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional

# 🔹 Schéma pour la création (requête POST) - SANS username
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""
    role: Optional[str] = "researcher"
    status: Optional[str] = "pending"

# 🔹 Schéma pour la sortie (réponse API)
class UserOut(BaseModel):
    id: int
    email: EmailStr
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""
    role: str
    status: str
    
    model_config = ConfigDict(from_attributes=True)