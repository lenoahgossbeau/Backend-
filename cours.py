from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base

class Cours(Base):
    __tablename__ = "cours"
    
    id = Column(Integer, primary_key=True, index=True)
    # ⚠️ CORRECTION: Ajouter nullable=False
    profile_id = Column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)  # ✅ Ajouter nullable=False
    description = Column(Text, nullable=True)  # ✅ Changer String en Text
    curricula = Column(String(255), nullable=True)
    
    profile = relationship("Profile", back_populates="cours")