# schemas/audit.py
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class AuditOut(BaseModel):
    id: int
    user_id: int
    user_role: str
    action_description: str
    created_at: datetime
    
    # ✅ Syntaxe Pydantic v2
    model_config = ConfigDict(from_attributes=True)