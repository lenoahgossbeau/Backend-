from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
from database import get_db
from models.audit import Audit
from models.user import User
from auth.jwt import get_current_user

router = APIRouter(prefix="/admin/audit", tags=["Admin Audit"])

@router.get("/logs")
def get_audit_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    
    logs = db.query(Audit).order_by(Audit.date.desc()).offset(offset).limit(limit).all()
    total = db.query(Audit).count()
    
    return {
        "total": total,
        "logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "user_role": log.user_role,
                "action_description": log.action_description,
                "date": log.date.isoformat() if log.date else None
            }
            for log in logs
        ]
    }