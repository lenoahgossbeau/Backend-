# models/academic_career.py - CODE COMPLET CORRIGÉ
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class AcademicCareer(Base):
    __tablename__ = "academic_careers"
    
    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    year = Column(Integer, nullable=False)
    title_formation = Column(String(255), nullable=False)
    diplome = Column(String(255), nullable=True)  # ⬅️ EN FRANÇAIS
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relation
    profile = relationship("Profile", back_populates="academic_careers")
    
    def __repr__(self):
        return f"<AcademicCareer {self.year} - {self.title_formation}>"