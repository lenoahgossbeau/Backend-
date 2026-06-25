from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"))
    start_date = Column(String(20))
    end_date = Column(String(20))
    type = Column(String(50))
    payment_method = Column(String(50))

    profile = relationship("Profile", back_populates="subscription")
