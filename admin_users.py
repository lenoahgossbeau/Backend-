from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from sqlalchemy.orm import Session
from io import StringIO
import csv
from datetime import datetime

from database import get_db
from models.user import User
from models.audit import Audit
from auth.jwt import get_current_user
from fastapi.templating import Jinja2Templates

admin_users_router = APIRouter(
    prefix="/admin/users",
    tags=["Admin Users"]
)

templates = Jinja2Templates(directory="templates")

# ======================
# LISTE DES UTILISATEURS (JSON) avec audit
# ======================
@admin_users_router.get("/")
def list_users(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    role: str = Query(None),
    status: str = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")

    query = db.query(User)

    if role:
        query = query.filter(User.role == role)
    if status:
        query = query.filter(User.status == status)

    total = query.count()
    users = query.offset((page - 1) * per_page).limit(per_page).all()

    # ✅ Audit log : consultation avec filtres et pagination
    audit_log = Audit(
        user_id=current_user.id,
        user_role=current_user.role,
        action_description=f"Consultation utilisateurs (role={role}, status={status}, page={page})",
        ip=request.client.host,
        date=datetime.utcnow()
    )
    db.add(audit_log)
    db.commit()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "role": u.role,
                "status": u.status
            }
            for u in users
        ]
    }

# ======================
# EXPORT CSV avec audit
# ======================
@admin_users_router.get("/export")
def export_users(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    role: str = Query(None),
    status: str = Query(None)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")

    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if status:
        query = query.filter(User.status == status)

    users = query.all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Email", "Role", "Status"])
    for u in users:
        writer.writerow([u.id, u.email, u.role, u.status])

    output.seek(0)

    # ✅ Audit log : export CSV avec filtres
    audit_log = Audit(
        user_id=current_user.id,
        user_role=current_user.role,
        action_description=f"Export CSV utilisateurs (role={role}, status={status})",
        ip=request.client.host,
        date=datetime.utcnow()
    )
    db.add(audit_log)
    db.commit()

    return StreamingResponse(output, media_type="text/csv", headers={
        "Content-Disposition": "attachment; filename=users_export.csv"
    })

# ======================
# PAGE HTML
# ======================
@admin_users_router.get("/page", response_class=HTMLResponse)
def users_page(request: Request, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    return templates.TemplateResponse(request, "users.html")
