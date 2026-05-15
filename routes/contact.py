from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from database import get_db
from models.contact_message import ContactMessage
from models.user import User

router = APIRouter(prefix="/contact", tags=["Contact"])

class ContactForm(BaseModel):
    name: str
    email: EmailStr
    message: str
    recipient_email: EmailStr

@router.post("/send", status_code=201)
def send_contact_message(data: ContactForm, db: Session = Depends(get_db)):
    # Trouver le chercheur destinataire
    recipient = db.query(User).filter(User.email == data.recipient_email, User.role == "researcher").first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Chercheur destinataire non trouvé")
    
    new_message = ContactMessage(
        name=data.name,
        email=data.email,
        message=data.message,
        recipient_user_id=recipient.id
    )
    db.add(new_message)
    db.commit()
    return {"message": "Message envoyé avec succès"}