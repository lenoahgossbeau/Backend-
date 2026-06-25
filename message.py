# schemas/message.py
from pydantic import BaseModel, ConfigDict

class MessageBase(BaseModel):
    subject: str
    content: str

class MessageCreate(MessageBase):
    pass

class MessageUpdate(BaseModel):
    status: str  # ex: "pending", "read", "archived"

class MessageOut(MessageBase):
    id: int
    user_id: int
    status: str
    
    # ✅ Syntaxe Pydantic v2
    model_config = ConfigDict(from_attributes=True)