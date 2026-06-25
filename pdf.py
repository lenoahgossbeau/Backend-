# routes/pdf.py - VERSION CORRIGÉE
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import io
import traceback

from database import get_db
from models.user import User
from models.audit import Audit
from models.message_contact import MessageContact
from models.publication import Publication
from models.project import Project
from models.cours import Cours
from auth.jwt import get_current_user
from pydantic import BaseModel

# Import pour génération PDF
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("⚠️ ReportLab non installé. Pour générer des PDFs: pip install reportlab")

router = APIRouter(prefix="/api/pdf", tags=["PDF"])

class PDFRequest(BaseModel):
    title: str = "Rapport"
    content: str = ""
    data_type: str = "dashboard"  # dashboard, audits, users, etc.
    filters: dict = {}

# ===================== GÉNÉRATION PDF DU DASHBOARD =====================
@router.post("/generate")
async def generate_pdf_report(
    request: PDFRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Génère un PDF avec les données demandées"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    if not PDF_AVAILABLE:
        raise HTTPException(
            status_code=501, 
            detail="Génération PDF non disponible. Installez ReportLab: pip install reportlab"
        )
    
    try:
        # Créer le buffer pour le PDF
        buffer = io.BytesIO()
        
        # Créer le document PDF
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        
        # Style personnalisé pour le titre
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2c3e50')
        )
        
        # Style pour les sous-titres
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            spaceBefore=20,
            textColor=colors.HexColor('#34495e')
        )
        
        # Style pour le texte normal
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=12
        )
        
        # 1. Titre
        elements.append(Paragraph(request.title, title_style))
        elements.append(Spacer(1, 20))
        
        # 2. Métadonnées
        meta_text = f"""
        <b>Généré le:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}<br/>
        <b>Généré par:</b> {current_user.email}<br/>
        <b>Type de rapport:</b> {request.data_type}
        """
        elements.append(Paragraph(meta_text, normal_style))
        elements.append(Spacer(1, 30))
        
        # 3. Contenu selon le type
        if request.data_type == "dashboard":
            elements.extend(generate_dashboard_content(db, subtitle_style, normal_style))
        elif request.data_type == "audits":
            elements.extend(generate_audits_content(db, subtitle_style, normal_style, request.filters))
        elif request.data_type == "users":
            elements.extend(generate_users_content(db, subtitle_style, normal_style))
        else:
            # Contenu personnalisé
            if request.content:
                elements.append(Paragraph("Contenu:", subtitle_style))
                elements.append(Paragraph(request.content, normal_style))
        
        # 4. Pied de page
        elements.append(Spacer(1, 50))
        footer_text = f"""
        <i>Document généré automatiquement par le système Portfolio FastAPI<br/>
        {datetime.now().strftime('%d/%m/%Y')} - Page 1/1</i>
        """
        elements.append(Paragraph(footer_text, ParagraphStyle(
            'Footer',
            parent=styles['Italic'],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER
        )))
        
        # Générer le PDF
        doc.build(elements)
        
        # Retourner le PDF
        buffer.seek(0)
        pdf_data = buffer.getvalue()
        buffer.close()
        
        filename = f"{request.title.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return Response(
            content=pdf_data,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/pdf"
            }
        )
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur génération PDF: {str(e)[:200]}")

def generate_dashboard_content(db, subtitle_style, normal_style):
    """Génère le contenu du dashboard pour le PDF"""
    elements = []
    
    try:
        # Récupérer les statistiques avec try/except
        total_users = db.query(User).count()
        total_audits = db.query(Audit).count()
        total_messages = db.query(MessageContact).count()
        
        # Variables avec gestion d'erreur
        total_publications = 0
        total_projects = 0
        total_cours = 0
        
        try:
            total_publications = db.query(Publication).count()
        except:
            pass
            
        try:
            total_projects = db.query(Project).count()
        except:
            pass
            
        try:
            total_cours = db.query(Cours).count()
        except:
            pass
        
        # Titre section
        elements.append(Paragraph("Statistiques du Dashboard", subtitle_style))
        
        # Tableau des statistiques
        data = [
            ["Statistique", "Valeur"],
            ["Nombre d'utilisateurs", str(total_users)],
            ["Nombre d'audits", str(total_audits)],
            ["Nombre de messages", str(total_messages)],
            ["Nombre de publications", str(total_publications)],
            ["Nombre de projets", str(total_projects)],
            ["Nombre de cours", str(total_cours)]
        ]
        
        table = Table(data, colWidths=[3*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 30))
        
        # Utilisateurs par rôle
        elements.append(Paragraph("Utilisateurs par rôle", subtitle_style))
        
        users_by_role = db.query(User.role, func.count(User.id)).group_by(User.role).all()
        
        role_data = [["Rôle", "Nombre"]]
        for role, count in users_by_role:
            if role:  # Filtrer les rôles None
                role_data.append([role, str(count)])
        
        if len(role_data) > 1:  # S'il y a des données
            role_table = Table(role_data, colWidths=[2.5*inch, 2.5*inch])
            role_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            
            elements.append(role_table)
        else:
            elements.append(Paragraph("Aucune donnée disponible", normal_style))
        
    except Exception as e:
        traceback.print_exc()
        elements.append(Paragraph("Erreur lors de la récupération des données", subtitle_style))
        elements.append(Paragraph(str(e)[:200], normal_style))
    
    return elements

def generate_audits_content(db, subtitle_style, normal_style, filters):
    """Génère le contenu des audits pour le PDF"""
    elements = []
    
    try:
        elements.append(Paragraph("Journal des audits", subtitle_style))
        
        # Récupérer les audits
        query = db.query(Audit).order_by(Audit.date.desc())
        
        if filters.get("limit"):
            try:
                limit = int(filters["limit"])
                query = query.limit(min(limit, 100))
            except:
                pass
        else:
            query = query.limit(50)
        
        audits = query.all()
        
        elements.append(Paragraph(f"Total d'audits affichés: {len(audits)}", normal_style))
        elements.append(Spacer(1, 15))
        
        # Tableau des audits
        if audits:
            audit_data = [["Date", "Utilisateur (Rôle)", "Action"]]
            
            for audit in audits:
                date_str = audit.date.strftime('%d/%m/%Y %H:%M') if audit.date else "N/A"
                user_info = f"ID: {audit.user_id} ({audit.user_role})"
                action = audit.action_description[:100] if audit.action_description else "N/A"
                audit_data.append([date_str, user_info, action])
            
            audit_table = Table(audit_data, colWidths=[1.5*inch, 2*inch, 3*inch])
            audit_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            
            elements.append(audit_table)
        else:
            elements.append(Paragraph("Aucun audit trouvé", normal_style))
        
    except Exception as e:
        traceback.print_exc()
        elements.append(Paragraph("Erreur lors de la récupération des audits", normal_style))
    
    return elements

def generate_users_content(db, subtitle_style, normal_style):
    """Génère le contenu des utilisateurs pour le PDF"""
    elements = []
    
    try:
        elements.append(Paragraph("Liste des utilisateurs", subtitle_style))
        
        # Récupérer les utilisateurs
        users = db.query(User).order_by(User.created_at.desc()).limit(100).all()
        
        elements.append(Paragraph(f"Total d'utilisateurs: {len(users)}", normal_style))
        elements.append(Spacer(1, 15))
        
        # Tableau des utilisateurs
        if users:
            user_data = [["ID", "Email", "Rôle", "Statut", "Créé le"]]
            
            for user in users:
                created_str = user.created_at.strftime('%d/%m/%Y') if user.created_at else "N/A"
                user_data.append([
                    str(user.id),
                    user.email,
                    user.role or "N/A",
                    user.status or "N/A",
                    created_str
                ])
            
            user_table = Table(user_data, colWidths=[0.5*inch, 2.5*inch, 1*inch, 1*inch, 1*inch])
            user_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            
            elements.append(user_table)
        else:
            elements.append(Paragraph("Aucun utilisateur trouvé", normal_style))
        
    except Exception as e:
        traceback.print_exc()
        elements.append(Paragraph("Erreur lors de la récupération des utilisateurs", normal_style))
    
    return elements

# ===================== PDF SIMPLE POUR TEST =====================
@router.get("/test")
async def generate_test_pdf(
    current_user: User = Depends(get_current_user)
):
    """Génère un PDF de test simple"""
    if not PDF_AVAILABLE:
        raise HTTPException(
            status_code=501, 
            detail="ReportLab non installé"
        )
    
    try:
        # Créer un PDF simple avec reportlab
        buffer = io.BytesIO()
        
        # Version simple avec canvas
        c = canvas.Canvas(buffer, pagesize=letter)
        
        # Titre
        c.setFont("Helvetica-Bold", 24)
        c.drawString(100, 750, "Test PDF - Portfolio FastAPI")
        
        # Sous-titre
        c.setFont("Helvetica", 14)
        c.drawString(100, 720, f"Généré le: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        c.drawString(100, 700, f"Utilisateur: {current_user.email}")
        
        # Contenu
        c.setFont("Helvetica", 12)
        c.drawString(100, 650, "Ceci est un test de génération PDF.")
        c.drawString(100, 630, "Toutes les fonctionnalités PDF sont opérationnelles.")
        
        # Footer
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(100, 50, "Document généré automatiquement")
        
        c.showPage()
        c.save()
        
        buffer.seek(0)
        pdf_data = buffer.getvalue()
        buffer.close()
        
        return Response(
            content=pdf_data,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=test_document.pdf",
                "Content-Type": "application/pdf"
            }
        )
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur génération PDF test: {str(e)}")