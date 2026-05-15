from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from auth.jwt import create_activation_token
from pydantic import BaseModel
from email_service import send_activation_email_brevo

router = APIRouter(prefix="/admin/users", tags=["Admin Activation"])

class EmailRequest(BaseModel):
    email: str

@router.post("/activation-link")
def get_activation_link(payload: EmailRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    token = create_activation_token(user.email)
    link = f"http://localhost:3000/auth/activate?token={token}"
    
    # Utilisation de Brevo (au lieu de Resend)
    email_sent = send_activation_email_brevo(payload.email, link, getattr(user, 'first_name', ''))
    
    return {
        "activation_link": link,
        "email_sent": email_sent,
        "message": "Email d'activation envoyé" if email_sent else "Erreur d'envoi"
    }