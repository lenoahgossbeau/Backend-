from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Audit(Base):
    __tablename__ = "audits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_role = Column(String(20), nullable=False)
    action_description = Column(String(500), nullable=False)
    date = Column(TIMESTAMP, default=datetime.utcnow)  # ✅ conforme à ta base

    user = relationship("User", back_populates="audits")
