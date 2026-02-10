from sqlalchemy import Column, Integer, String, ForeignKey, JSON, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class Publication(Base):
    __tablename__ = "publications"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)

    # ⚫ CONFORME CAHIER DES CHARGES
    year = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    coauthor = Column(JSON, nullable=False, default=list)

    # 🟢 OPTIONNELS
    journal = Column(String(300))
    doi = Column(String(100))

    created_at = Column(TIMESTAMP, server_default=func.now())

    # ======================
    # RELATIONS
    # ======================
    profile = relationship("Profile", back_populates="publications")

    comments = relationship(
        "Comment",
        back_populates="publication",
        cascade="all, delete-orphan"
    )
