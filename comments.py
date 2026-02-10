from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.comment import Comment
from models.audit import Audit
from models.user import User
from schemas.comment import CommentCreate, CommentOut
from auth.dependencies import get_current_user

router = APIRouter(prefix="/comments", tags=["Comments"])

@router.post("/", response_model=CommentOut)
def add_comment(comment: CommentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_comment = Comment(
        content=comment.content,
        publication_id=comment.publication_id,
        user_id=current_user.id
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    # Audit log
    audit_log = Audit(
        user_id=current_user.id,
        user_role=current_user.role,
        action_description=f"Commentaire ajouté sur publication {comment.publication_id}"
    )
    db.add(audit_log)
    db.commit()

    return new_comment

@router.get("/{publication_id}", response_model=list[CommentOut])
def get_comments(publication_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Comment).filter(Comment.publication_id == publication_id).all()
