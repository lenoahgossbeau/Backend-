from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class MessageContact(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)

    # ✅ Ajout du champ sender_name
    sender_name = Column(String(100), nullable=False)
    sender_email = Column(String(100), nullable=False)
    message = Column(String(1000), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relation inverse vers Profile
    profile = relationship("Profile", back_populates="messages")
