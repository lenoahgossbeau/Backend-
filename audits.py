from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.audit import Audit
from schemas.audit import AuditOut
from auth.dependencies import get_current_admin
from datetime import datetime
import csv
import io
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/audits", tags=["Audits"])

# ================== LISTER LES AUDITS AVEC FILTRES ET PAGINATION (ADMIN) ==================
@router.get(
    "/", 
    response_model=list[AuditOut], 
    summary="Lister les audits", 
    description="Permet à un administrateur de consulter les logs d'audit avec filtres et pagination."
)
def get_audits(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin),
    role: str | None = Query(None, description="Filtrer par rôle utilisateur"),
    start_date: datetime | None = Query(None, description="Filtrer à partir de cette date"),
    end_date: datetime | None = Query(None, description="Filtrer jusqu’à cette date"),
    skip: int = 0,
    limit: int = 20
):
    query = db.query(Audit)

    if role:
        query = query.filter(Audit.user_role == role)
    if start_date:
        query = query.filter(Audit.created_at >= start_date)
    if end_date:
        query = query.filter(Audit.created_at <= end_date)

    audits = query.order_by(Audit.created_at.desc()).offset(skip).limit(limit).all()
    return audits

# ================== EXPORT CSV (ADMIN) ==================
@router.get(
    "/export/csv", 
    summary="Exporter les audits en CSV", 
    description="Permet à un administrateur d'exporter les logs d'audit filtrés en CSV."
)
def export_audits_csv(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin),
    role: str | None = Query(None, description="Filtrer par rôle utilisateur"),
    start_date: datetime | None = Query(None, description="Filtrer à partir de cette date"),
    end_date: datetime | None = Query(None, description="Filtrer jusqu’à cette date")
):
    query = db.query(Audit)

    if role:
        query = query.filter(Audit.user_role == role)
    if start_date:
        query = query.filter(Audit.created_at >= start_date)
    if end_date:
        query = query.filter(Audit.created_at <= end_date)

    audits = query.order_by(Audit.created_at.desc()).all()

    if not audits:
        raise HTTPException(status_code=404, detail="Aucun audit trouvé ❌")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "User ID", "Role", "Action", "Date"])
    for audit in audits:
        writer.writerow([audit.id, audit.user_id, audit.user_role, audit.action_description, audit.created_at])

    output.seek(0)
    return StreamingResponse(
        output, 
        media_type="text/csv", 
        headers={"Content-Disposition": "attachment; filename=audits.csv"}
    )
