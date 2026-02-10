# auth/schemas.py
from pydantic import BaseModel, EmailStr, ConfigDict

# ======================
# REGISTER
# ======================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str


# ======================
# LOGIN
# ======================

class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ======================
# TOKEN
# ======================

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ======================
# USER RESPONSE
# ======================

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: str
    status: str
    
    # ✅ Syntaxe Pydantic v2
    model_config = ConfigDict(from_attributes=True)