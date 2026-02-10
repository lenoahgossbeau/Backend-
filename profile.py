from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Informations personnelles (optionnelles)
    first_name = Column(String(50))
    last_name = Column(String(50))
    gender = Column(String(10))
    
    # ⚫ CONFORME CAHIER DES CHARGES
    grade = Column(String(50), nullable=False)
    specialite = Column(String(100), nullable=True)
    
    # Optionnels
    diplome = Column(String(100))
    description = Column(Text)
    profile_picture = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # =========================
    # RELATIONS
    # =========================
    user = relationship("User", back_populates="profile")

    # Relations 1→N (CONFORME CAHIER DES CHARGES)
    publications = relationship(
        "Publication",
        back_populates="profile",
        cascade="all, delete-orphan"
    )

    projects = relationship(
        "Project",
        back_populates="profile",
        cascade="all, delete-orphan"
    )

    cours = relationship(
        "Cours",
        back_populates="profile",
        cascade="all, delete-orphan"
    )

    distinctions = relationship(
        "Distinction",
        back_populates="profile",
        cascade="all, delete-orphan"
    )

    academic_careers = relationship(
        "AcademicCareer", 
        back_populates="profile",
        cascade="all, delete-orphan"
    )
    
    media_artefacts = relationship(
        "MediaArtefact", 
        back_populates="profile",
        cascade="all, delete-orphan"
    )

    messages = relationship(
        "MessageContact",
        back_populates="profile",
        cascade="all, delete-orphan"
    )

    subscription = relationship(
        "Subscription",
        uselist=False,
        back_populates="profile"
    )
    
    def __repr__(self):
        return f"<Profile(id={self.id}, user_id={self.user_id}, grade={self.grade})>"
