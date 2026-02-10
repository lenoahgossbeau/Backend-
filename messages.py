from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.message_contact import MessageContact
from models.audit import Audit
from models.user import User
from schemas.message import MessageCreate, MessageOut, MessageUpdate
from auth.dependencies import get_current_normal_user, get_current_admin
import csv
import io
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/messages", tags=["Messages"])

# ================== ENVOYER UN MESSAGE (USER) ==================
@router.post("/", response_model=MessageOut, summary="Envoyer un message", description="Permet à un utilisateur connecté d'envoyer un message.")
def send_message(message: MessageCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_normal_user)):
    new_message = MessageContact(
        subject=message.subject,
        content=message.content,
        user_id=current_user.id,
        status="pending"  # ✅ statut par défaut
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    # Audit log
    audit_log = Audit(
        user_id=current_user.id,
        user_role=current_user.role,
        action_description=f"Message envoyé: {message.subject}"
    )
    db.add(audit_log)
    db.commit()

    return new_message

# ================== LISTER MES MESSAGES (USER) ==================
@router.get("/", response_model=list[MessageOut], summary="Lister mes messages", description="Retourne tous les messages envoyés par l'utilisateur connecté.")
def get_my_messages(db: Session = Depends(get_db), current_user: User = Depends(get_current_normal_user)):
    return db.query(MessageContact).filter(MessageContact.user_id == current_user.id).all()

# ================== METTRE À JOUR LE STATUT (ADMIN) ==================
@router.put("/{message_id}", response_model=MessageOut, summary="Mettre à jour le statut d'un message", description="Permet à un administrateur de modifier le statut d'un message.")
def update_message_status(message_id: int, data: MessageUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    message = db.query(MessageContact).filter(MessageContact.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message introuvable ❌")
    message.status = data.status
    db.commit()
    db.refresh(message)

    # Audit log
    audit_log = Audit(
        user_id=current_user.id,
        user_role=current_user.role,
        action_description=f"Statut du message {message_id} mis à jour → {data.status}"
    )
    db.add(audit_log)
    db.commit()

    return message

# ================== EXPORT CSV (ADMIN) ==================
@router.get("/export/csv", summary="Exporter les messages en CSV", description="Permet à un administrateur d'exporter tous les messages en CSV.")
def export_messages_csv(db: Session = Depends(get_db), current_user: User = Depends(get_current_admin)):
    messages = db.query(MessageContact).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Subject", "Content", "User ID", "Status", "Created At"])
    for msg in messages:
        writer.writerow([msg.id, msg.subject, msg.content, msg.user_id, msg.status, msg.created_at])

    output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=messages.csv"})
