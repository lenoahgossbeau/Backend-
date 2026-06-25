# schemas/comment.py
from pydantic import BaseModel, ConfigDict

class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    pass  # publication_id injecté via route

class CommentOut(CommentBase):
    id: int
    publication_id: int
    user_id: int
    
    # ✅ Syntaxe Pydantic v2
    model_config = ConfigDict(from_attributes=True)