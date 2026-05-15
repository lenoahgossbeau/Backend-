# models/user.py
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)

    role = Column(String(20), default="researcher", nullable=False, index=True)
    status = Column(String(20), default="inactive", nullable=False, index=True)
    is_active = Column(Boolean, default=False, nullable=False)

    activation_code = Column(String(100), nullable=True)
    slug = Column(String(100), unique=True, nullable=True)  # 👈 AJOUT POUR SOUS-DOMAINE

    # ======================
    # RELATIONS
    # ======================
    profile = relationship(
        "Profile",
        uselist=False,
        back_populates="user",
        cascade="all, delete-orphan"
    )

    audits = relationship(
        "Audit",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    comments = relationship(
        "Comment",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"