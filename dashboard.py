# routes/dashboard.py - VERSION FINALE CORRIGÉE
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import traceback

from database import get_db
from models.user import User
from models.audit import Audit
from models.message_contact import MessageContact
from models.publication import Publication
from models.project import Project
from models.cours import Cours
from models.comment import Comment
from models.distinction import Distinction
from models.academic_career import AcademicCareer
from models.media_artefact import MediaArtefact
from auth.jwt import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

def reset_db_session(db: Session):
    """Réinitialise la session DB en cas d'erreur de transaction"""
    try:
        db.rollback()
    except:
        pass

# ===================== STATISTIQUES DU DASHBOARD =====================
@router.get("/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retourne toutes les statistiques du dashboard"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    try:
        # Réinitialiser la session au cas où
        reset_db_session(db)
        
        # Statistiques générales - version SÉCURISÉE
        stats = {
            "general": {
                "total_users": 0,
                "total_audits": 0,
                "total_messages": 0,
                "total_publications": 0,
                "total_projects": 0,
                "total_cours": 0,
                "total_comments": 0,
                "total_distinctions": 0,
                "total_academic": 0,
                "total_media": 0,
                "recent_audits_7d": 0,
            },
            "users_by_role": {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Essayer chaque requête séparément
        try:
            stats["general"]["total_users"] = db.query(User).count()
        except Exception as e:
            print(f"⚠️  Erreur comptage users: {e}")
            db.rollback()
        
        try:
            stats["general"]["total_audits"] = db.query(Audit).count()
        except Exception as e:
            print(f"⚠️  Erreur comptage audits: {e}")
            db.rollback()
        
        try:
            stats["general"]["total_messages"] = db.query(MessageContact).count()
        except Exception as e:
            print(f"⚠️  Erreur comptage messages: {e}")
            db.rollback()
        
        # Compter les autres modèles avec try/except
        models_to_count = [
            (Publication, "total_publications"),
            (Project, "total_projects"),
            (Cours, "total_cours"),
            (Comment, "total_comments"),
            (Distinction, "total_distinctions"),
            (AcademicCareer, "total_academic"),
            (MediaArtefact, "total_media")
        ]
        
        for model, key in models_to_count:
            try:
                count = db.query(model).count()
                stats["general"][key] = count
            except Exception as e:
                print(f"⚠️  Erreur comptage {key}: {e}")
                db.rollback()
                stats["general"][key] = 0
        
        # Utilisateurs par rôle - version sécurisée
        try:
            users_by_role = db.query(User.role, func.count(User.id)).group_by(User.role).all()
            stats["users_by_role"] = {role: count for role, count in users_by_role if role}
        except Exception as e:
            print(f"⚠️  Erreur users par rôle: {e}")
            db.rollback()
            stats["users_by_role"] = {}
        
        # Audits récents (7 derniers jours)
        try:
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_audits = db.query(Audit).filter(Audit.date >= week_ago).count()
            stats["general"]["recent_audits_7d"] = recent_audits
        except Exception as e:
            print(f"⚠️  Erreur audits récents: {e}")
            db.rollback()
        
        return stats
        
    except Exception as e:
        traceback.print_exc()
        # Retourner des données minimales plutôt qu'une erreur 500
        return {
            "general": {
                "total_users": 0,
                "total_audits": 0,
                "total_messages": 0,
                "total_publications": 0,
                "total_projects": 0,
                "total_cours": 0,
                "total_comments": 0,
                "total_distinctions": 0,
                "total_academic": 0,
                "total_media": 0,
                "recent_audits_7d": 0,
            },
            "users_by_role": {},
            "timestamp": datetime.utcnow().isoformat(),
            "note": "Données limitées en raison d'une erreur technique"
        }

# ===================== DONNÉES POUR GRAPHIQUES =====================
@router.get("/charts")
async def get_chart_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = 30
):
    """Données pour les graphiques du dashboard"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    try:
        # Audits par jour (30 derniers jours)
        start_date = datetime.utcnow().date() - timedelta(days=days)
        
        audit_stats = db.query(
            func.date(Audit.date).label('date'),
            func.count(Audit.id).label('count')
        ).filter(
            Audit.date >= start_date
        ).group_by(
            func.date(Audit.date)
        ).order_by('date').all()
        
        # Formater pour le graphique
        audit_dates = []
        audit_counts = []
        for stat in audit_stats:
            if stat.date:
                audit_dates.append(str(stat.date))
                audit_counts.append(stat.count or 0)
        
        # Messages par mois (version compatible)
        message_stats = []
        try:
            # Essayer PostgreSQL
            message_stats = db.query(
                func.date_trunc('month', MessageContact.created_at).label('month'),
                func.count(MessageContact.id).label('count')
            ).group_by(
                func.date_trunc('month', MessageContact.created_at)
            ).order_by('month').all()
        except:
            try:
                # Essayer SQLite
                message_stats = db.query(
                    func.strftime('%Y-%m', MessageContact.created_at).label('month'),
                    func.count(MessageContact.id).label('count')
                ).group_by(
                    func.strftime('%Y-%m', MessageContact.created_at)
                ).order_by('month').all()
            except Exception as e:
                print(f"⚠️  Erreur messages par mois: {e}")
        
        message_months = []
        message_counts = []
        for stat in message_stats:
            if hasattr(stat.month, 'strftime'):
                message_months.append(stat.month.strftime('%Y-%m'))
            else:
                message_months.append(str(stat.month))
            message_counts.append(stat.count or 0)
        
        return {
            "audits": {
                "labels": audit_dates,
                "data": audit_counts,
                "title": f"Audits ({days} derniers jours)"
            },
            "messages": {
                "labels": message_months,
                "data": message_counts,
                "title": "Messages par mois"
            }
        }
        
    except Exception as e:
        traceback.print_exc()
        return {
            "audits": {"labels": [], "data": [], "title": "Erreur"},
            "messages": {"labels": [], "data": [], "title": "Erreur"}
        }

# ===================== ACTIVITÉS RÉCENTES =====================
@router.get("/recent-activities")
async def get_recent_activities(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 10
):
    """Activités récentes pour le dashboard"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    try:
        # Récupérer les audits récents
        recent_audits = db.query(Audit).order_by(Audit.date.desc()).limit(limit).all()
        
        # Formater les résultats
        activities = []
        for audit in recent_audits:
            activities.append({
                "id": audit.id,
                "date": audit.date.isoformat() if audit.date else None,
                "user_id": audit.user_id,
                "user_role": audit.user_role,
                "action": audit.action_description or "Action non spécifiée",
                "type": "audit"
            })
        
        # Récupérer les messages récents
        try:
            recent_messages = db.query(MessageContact).order_by(
                MessageContact.created_at.desc()
            ).limit(5).all()
            
            for message in recent_messages:
                activities.append({
                    "id": message.id,
                    "date": message.created_at.isoformat() if message.created_at else None,
                    "sender": message.sender_email,
                    "action": f"Nouveau message de {message.sender_name or 'Inconnu'}",
                    "type": "message"
                })
        except Exception as e:
            print(f"⚠️  Erreur récupération messages: {e}")
        
        # Trier par date
        activities.sort(key=lambda x: x["date"] or "", reverse=True)
        
        return {
            "activities": activities[:limit],
            "total": len(activities)
        }
        
    except Exception as e:
        traceback.print_exc()
        return {"activities": [], "total": 0}