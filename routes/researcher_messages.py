from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.user import User
from models.contact_message import ContactMessage
from auth.jwt import get_current_user

router = APIRouter(prefix="/researcher", tags=["Researcher"])

@router.get("/messages")
def get_messages(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "researcher":
        raise HTTPException(status_code=403, detail="Accès réservé aux chercheurs")
    
    messages = db.query(ContactMessage).filter(ContactMessage.recipient_user_id == current_user.id).order_by(ContactMessage.created_at.desc()).all()
    return messages

@router.put("/messages/{message_id}/read")
def mark_as_read(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "researcher":
        raise HTTPException(status_code=403, detail="Accès réservé aux chercheurs")
    
    message = db.query(ContactMessage).filter(
        ContactMessage.id == message_id,
        ContactMessage.recipient_user_id == current_user.id
    ).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message non trouvé")
    
    message.is_read = 1
    db.commit()
    return {"message": "Marqué comme lu"}

# ================== PUBLIER LE PROFIL ==================
@router.post("/publish")
def publish_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Publie le profil du chercheur (le rend visible au public)"""
    
    if current_user.role != "researcher":
        raise HTTPException(status_code=403, detail="Seuls les chercheurs peuvent publier leur profil")
    
    # Changer le statut de pending à active
    current_user.status = "active"
    current_user.is_active = True
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "success": True,
        "message": "Votre profil a été publié avec succès et est maintenant visible au public",
        "status": current_user.status
    }