from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class MediaArtefact(Base):
    __tablename__ = "media_artefacts"
    
    id = Column(Integer, primary_key=True, index=True)
    # ⚠️ CORRECTION CRITIQUE: Ajouter profile_id avec ForeignKey
    profile_id = Column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)  # ✅ Ajouter description optionnelle
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ⚠️ CORRECTION CRITIQUE: Ajouter la relation
    profile = relationship("Profile", back_populates="media_artefacts")
    
    def __repr__(self):
        return f"<MediaArtefact {self.name}>"