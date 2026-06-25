# schemas/user.py
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional

# 🔹 Schéma de base (champs communs)
class UserBase(BaseModel):
    email: EmailStr
    username: str                # ✅ Ajout du champ username (utilisé dans register)
    role: Optional[str] = "user" # ✅ Valeur par défaut cohérente
    status: Optional[str] = "active"

# 🔹 Schéma pour la création (requête POST)
class UserCreate(UserBase):
    password: str                # ✅ Mot de passe obligatoire pour l'inscription

# 🔹 Schéma pour la sortie (réponse API)
class UserOut(UserBase):
    id: int
    
    # ✅ Syntaxe Pydantic v2
    model_config = ConfigDict(from_attributes=True)