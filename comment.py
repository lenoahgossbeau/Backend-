# models/comment.py
from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Clés étrangères
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    publication_id = Column(Integer, ForeignKey("publications.id", ondelete="CASCADE"), nullable=True)
    
    # Relations - CORRECTION: 'comments' doit correspondre à User.comments
    user = relationship("User", back_populates="comments")  # ✅ CORRECT
    project = relationship("Project", back_populates="comments")
    publication = relationship("Publication", back_populates="comments")
    
    def __repr__(self):
        return f"<Comment(id={self.id}, user_id={self.user_id})>"