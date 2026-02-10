from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Text, Numeric, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)

    # ⚫ CONFORME CAHIER DES CHARGES
    year = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    coauthor = Column(JSON, nullable=False, default=list)

    # 🟢 OPTIONNELS
    description = Column(Text)
    budget = Column(Numeric(10, 2))
    status = Column(String(50))

    created_at = Column(TIMESTAMP, server_default=func.now())

    # ======================
    # RELATIONS
    # ======================
    profile = relationship("Profile", back_populates="projects")

    comments = relationship(
        "Comment",
        back_populates="project",
        cascade="all, delete-orphan"
    )
