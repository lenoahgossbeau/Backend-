from sqlalchemy import Column, Integer, String, Text, DateTime
from database import Base
from datetime import datetime

class ContactMessage(Base):
    __tablename__ = "contact_messages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Integer, default=0)
    recipient_user_id = Column(Integer, nullable=True)  # 👈 NOUVEAU