from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
from fastapi.templating import Jinja2Templates
from io import StringIO, BytesIO
import csv
from reportlab.lib.pagesizes import letter 
from reportlab.pdfgen import canvas

from database import get_db
from models.user import User
from models.refresh_token import RefreshToken
from models.audit import Audit
from auth.jwt import get_current_user
from auth.permissions import require_role

# Initialisation du router et des templates
admin_router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)
templates = Jinja2Templates(directory="templates")
# ======================
# UTILITAIRE D'AUDIT LOG
# ======================
def log_action(db: Session, current_user: User, request: Request, description: str):
    """
    Enregistre une action dans la table Audit pour assurer la traçabilité.
    """
    audit_log = Audit(
        user_id=current_user.id,
        user_role=current_user.role,
        action_description=description,
        date=datetime.utcnow()
    )
    db.add(audit_log)
    db.commit()
# ======================
# LISTE DES SESSIONS (JSON)
# ======================
@admin_router.get("/sessions", dependencies=[Depends(require_role("admin", "super_admin"))])
def list_sessions(db: Session = Depends(get_db)):
    sessions = db.query(RefreshToken).order_by(RefreshToken.created_at.desc()).all()
    return [
        {
            "id": s.id,
            "user_id": s.user_id,
            "token": s.token,
            "created_at": s.created_at,
            "revoked": s.revoked
        }
        for s in sessions
    ]

# ======================
# PAGE HTML DES SESSIONS
# ======================
@admin_router.get("/sessions/page", response_class=HTMLResponse, dependencies=[Depends(require_role("admin", "super_admin"))])
def sessions_page(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse("sessions.html", {
        "request": request,
        "current_user": current_user
    })

# ======================
# RÉVOQUER UNE SESSION
# ======================
@admin_router.post("/sessions/revoke/{session_id}", dependencies=[Depends(require_role("admin", "super_admin"))])
def revoke_session(session_id: int, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(RefreshToken).filter(RefreshToken.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable")

    session.revoked = True
    db.commit()

    # ✅ Audit log automatique
    log_action(db, current_user, request, f"Session {session_id} révoquée")

    return {"message": f"Session {session_id} révoquée ✅"}
# ======================
# STATISTIQUES AUDIT (JSON)
# ======================
@admin_router.get("/audit-stats", dependencies=[Depends(require_role("researcher", "admin", "super_admin"))])
def audit_stats(db: Session = Depends(get_db)):
    audits = db.query(Audit).all()
    stats = {}
    for a in audits:
        day = a.date.strftime("%Y-%m-%d")
        stats[day] = stats.get(day, 0) + 1

    return [{"date": d, "count": stats[d]} for d in sorted(stats.keys())]

# ======================
# PAGE HTML DES STATISTIQUES AUDIT
# ======================
@admin_router.get("/audit-stats/page", response_class=HTMLResponse, dependencies=[Depends(require_role("researcher", "admin", "super_admin"))])
def audit_stats_page(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse("audit_stats.html", {
        "request": request,
        "current_user": current_user
    })
# ======================
# PAGE HTML DU DASHBOARD ADMIN
# ======================
@admin_router.get("/dashboard", response_class=HTMLResponse, dependencies=[Depends(require_role("admin", "super_admin"))])
def dashboard_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.status == "active").count()
    inactive_users = db.query(User).filter(User.status == "inactive").count()
    active_sessions = db.query(RefreshToken).filter(RefreshToken.revoked == False).count()
    total_audits = db.query(Audit).count()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "current_user": current_user,
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": inactive_users,
        "active_sessions": active_sessions,
        "total_audits": total_audits
    })
# ======================
# EXPORT CSV DU DASHBOARD
# ======================
@admin_router.get("/dashboard/export/csv", dependencies=[Depends(require_role("admin", "super_admin"))])
def export_dashboard_csv(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # ✅ Audit log automatique
    log_action(db, current_user, request, "Export CSV du dashboard")

    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.status == "active").count()
    inactive_users = db.query(User).filter(User.status == "inactive").count()
    active_sessions = db.query(RefreshToken).filter(RefreshToken.revoked == False).count()
    total_audits = db.query(Audit).count()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Total utilisateurs", "Actifs", "Inactifs", "Sessions actives", "Total audits"])
    writer.writerow([total_users, active_users, inactive_users, active_sessions, total_audits])
    output.seek(0)

    return StreamingResponse(output, media_type="text/csv", headers={
        "Content-Disposition": "attachment; filename=dashboard_report.csv"
    })
# ======================
# EXPORT PDF DU DASHBOARD (stats seules)
# ======================
@admin_router.get("/dashboard/export/pdf", dependencies=[Depends(require_role("super_admin"))])
def export_dashboard_pdf(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # ✅ Audit log automatique
    log_action(db, current_user, request, "Export PDF du dashboard (stats seules)")

    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.status == "active").count()
    inactive_users = db.query(User).filter(User.status == "inactive").count()
    active_sessions = db.query(RefreshToken).filter(RefreshToken.revoked == False).count()
    total_audits = db.query(Audit).count()

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, 750, "Rapport Dashboard Admin")

    p.setFont("Helvetica", 12)
    p.drawString(100, 700, f"Total utilisateurs : {total_users}")
    p.drawString(100, 680, f"Utilisateurs actifs : {active_users}")
    p.drawString(100, 660, f"Utilisateurs inactifs : {inactive_users}")
    p.drawString(100, 640, f"Sessions actives : {active_sessions}")
    p.drawString(100, 620, f"Total audits : {total_audits}")

    p.showPage()
    p.save()
    buffer.seek(0)

    return StreamingResponse(buffer, media_type="application/pdf", headers={
        "Content-Disposition": "attachment; filename=dashboard_report.pdf"
    })
# ======================
# EXPORT PDF DU DASHBOARD AVEC GRAPHIQUE
# ======================
@admin_router.post("/dashboard/export/pdf-with-chart", dependencies=[Depends(require_role("super_admin"))])
def export_dashboard_pdf_with_chart(
    payload: dict,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    chart_base64 = payload.get("chart")
    if not chart_base64:
        raise HTTPException(status_code=400, detail="Image du graphique manquante")

    # ✅ Audit log automatique
    log_action(db, current_user, request, "Export PDF du dashboard avec graphique")

    # Récupérer les stats
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.status == "active").count()
    inactive_users = db.query(User).filter(User.status == "inactive").count()
    active_sessions = db.query(RefreshToken).filter(RefreshToken.revoked == False).count()
    total_audits = db.query(Audit).count()

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, 750, "Rapport Dashboard Admin (avec graphique)")

    p.setFont("Helvetica", 12)
    p.drawString(100, 700, f"Total utilisateurs : {total_users}")
    p.drawString(100, 680, f"Utilisateurs actifs : {active_users}")
    p.drawString(100, 660, f"Utilisateurs inactifs : {inactive_users}")
    p.drawString(100, 640, f"Sessions actives : {active_sessions}")
    p.drawString(100, 620, f"Total audits : {total_audits}")

    # Ajouter le graphique
    try:
        import base64
        from PIL import Image as PILImage
        import io

        chart_data = chart_base64.split(",")[1]
        chart_bytes = base64.b64decode(chart_data)
        chart_image = PILImage.open(io.BytesIO(chart_bytes))

        img_buffer = BytesIO()
        chart_image.save(img_buffer, format="PNG")
        img_buffer.seek(0)

        p.drawImage(img_buffer, 100, 400, width=400, height=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'insertion du graphique: {e}")

    p.showPage()
    p.save()
    buffer.seek(0)

    return StreamingResponse(buffer, media_type="application/pdf", headers={
        "Content-Disposition": "attachment; filename=dashboard_report_with_chart.pdf"
    })
# ======================
# AUDITS AVEC PAGINATION + FILTRES (JSON)
# ======================
@admin_router.get("/dashboard/audits", dependencies=[Depends(require_role("admin", "super_admin"))])
def latest_audits(
    page: int = 1,
    limit: int = 10,
    user_id: int | None = None,
    role: str | None = None,
    action: str | None = None,
    db: Session = Depends(get_db)
):
    # Construire la requête avec filtres
    query = db.query(Audit)
    if user_id:
        query = query.filter(Audit.user_id == user_id)
    if role:
        query = query.filter(Audit.user_role == role)
    if action:
        query = query.filter(Audit.action_description.ilike(f"%{action}%"))

    # Pagination
    total = query.count()
    audits = query.order_by(Audit.date.desc()).offset((page - 1) * limit).limit(limit).all()

    # Retour JSON
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "audits": [
            {
                "id": a.id,
                "user_id": a.user_id,
                "user_role": a.user_role,
                "action": a.action_description,
                "date": a.date.strftime("%Y-%m-%d %H:%M:%S")
            }
            for a in audits
        ]
    }
