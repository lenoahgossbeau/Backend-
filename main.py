# ===================== ENV =====================
from dotenv import load_dotenv
load_dotenv()  # ⚠️ DOIT ÊTRE TOUT EN HAUT

import traceback
print("🔧 Démarrage de l'application...")

try:
    # ===================== FASTAPI =====================
    from fastapi import (
        FastAPI, Request, Form, Depends,
        HTTPException, status, Response
    )
    from fastapi.responses import (
        HTMLResponse, RedirectResponse,
        StreamingResponse, JSONResponse
    )
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
    from starlette.middleware.sessions import SessionMiddleware
    from starlette.middleware.base import BaseHTTPMiddleware

    # ===================== CORE =====================
    from sqlalchemy.orm import Session
    from sqlalchemy import func, text  # AJOUT: text importé
    from datetime import datetime, date, timedelta
    import io, csv, os, time, sys
    from collections import defaultdict

    # ===================== DATABASE =====================
    from database import get_db
    from init_db import init_db

    # ===================== MODELS =====================
    # Importez d'abord la base
    from database import Base
    
    # Forcez l'import de tous les modèles AVANT les routeurs
    import models.user
    import models.refresh_token
    import models.profile
    import models.audit
    import models.publication
    import models.message_contact
    import models.comment
    import models.project
    import models.academic_career
    import models.media_artefact
    import models.distinction
    import models.cours
    import models.subscription
    
    # Maintenant importez les classes
    from models.user import User
    from models.profile import Profile
    from models.publication import Publication
    from models.message_contact import MessageContact
    from models.comment import Comment
    from models.audit import Audit
    from models.project import Project
    from models.academic_career import AcademicCareer
    from models.media_artefact import MediaArtefact
    from models.distinction import Distinction
    from models.cours import Cours
    from models.subscription import Subscription
    from routes.public_test import router as public_test_router

    # ===================== ROUTERS =====================
    from routes.user import router as user_router
    from routes.profile import router as profile_router
    from routes.publication import router as publication_router
    from auth.router import router as auth_router
    from routes.admin import admin_router
    from routes.admin_users import admin_users_router
    from routes.cours import router as cours_router
    from routes.auth import router as auth_routes_router
    from routes.dashboard import router as dashboard_router
    from routes.pdf import router as pdf_router
    from routes.project import router as project_router  # AJOUTÉ

    # ===================== AUTH =====================
    from auth.jwt import (
        get_current_user,
        get_current_user_optional
    )

    # ===================== APP =====================
    app = FastAPI(
        title="Portfolio FastAPI",
        description="Application web portfolio bilingue avec authentification et audit",
        version="1.0.0"
    )

    from fastapi.openapi.utils import get_openapi

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        }

        openapi_schema["security"] = [
            {"BearerAuth": []}
        ]

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    # ===================== INIT DB =====================
    try:
        print("🔧 Initialisation de la base de données...")
        init_db()
        print("✅ Base de données initialisée")
    except Exception as e:
        print(f"⚠️  Erreur lors de l'initialisation de la base: {e}")
        print("L'application continue en mode dégradé...")
        traceback.print_exc()

    # ===================== TEST CONFIG =====================
    TEST_MODE = "pytest" in sys.modules or os.getenv("ENV") == "test"

    # ===================== MIDDLEWARE =====================
    app.add_middleware(
        SessionMiddleware,
        secret_key=os.getenv("SESSION_SECRET_KEY", "dev_session_secret")
    )

    # ===================== STATIC & TEMPLATES =====================
    app.mount("/static", StaticFiles(directory="static"), name="static")
    templates = Jinja2Templates(directory="templates")

    # ===================== SECURITY HEADERS =====================
    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        start_time = time.time()
        response: Response = await call_next(request)
        process_time = time.time() - start_time
        
        # Headers de sécurité
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Process-Time"] = str(process_time)
        
        # HSTS seulement en HTTPS
        if request.url.scheme == "https" and not TEST_MODE:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # CORS pour les API
        if request.url.path.startswith("/api/"):
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"

        return response

    # ===================== RATE LIMIT =====================
    RATE_LIMIT = 100  # nombre maximum de requêtes
    WINDOW = 60  # fenêtre en secondes
    requests_counter = defaultdict(list)

    @app.middleware("http")
    async def rate_limiter(request: Request, call_next):
        # Routes qui ne sont PAS limitées
        excluded_paths = ["/health", "/docs", "/redoc", "/openapi.json", "/sitemap.xml", "/favicon.ico"]
        
        if not TEST_MODE:
            excluded_paths.extend(["/", "/about", "/contact", "/legal", "/privacy", 
                                   "/portfolio", "/publications", "/distinctions", 
                                   "/academic-career", "/api/info"])
        
        if request.url.path in excluded_paths:
            return await call_next(request)
        
        ip = request.client.host
        now = time.time()

        if ip in requests_counter:
            requests_counter[ip] = [t for t in requests_counter[ip] if now - t < WINDOW]

        if ip in requests_counter and len(requests_counter[ip]) >= RATE_LIMIT:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Trop de requêtes",
                    "message": f"Limite de {RATE_LIMIT} requêtes par {WINDOW} secondes atteinte",
                    "retry_after": WINDOW
                },
                headers={"Retry-After": str(WINDOW)}
            )
        
        if ip not in requests_counter:
            requests_counter[ip] = []
        requests_counter[ip].append(now)

        response = await call_next(request)
        remaining = RATE_LIMIT - len(requests_counter[ip])
        response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(int(now + WINDOW))
        
        return response

    # ===================== ROUTERS =====================
    # IMPORTANT: auth_routes_router d'abord (sans préfixe, donc /login)
    app.include_router(auth_routes_router)  # Celui-ci a /login à la racine
    
    # Ensuite les autres avec préfixes
    app.include_router(auth_router, prefix="/auth", tags=["Auth"])
    app.include_router(user_router, prefix="/users", tags=["Users"])
    app.include_router(profile_router, prefix="/profiles", tags=["Profiles"])
    app.include_router(publication_router, prefix="/publications", tags=["Publications"])
    app.include_router(project_router, prefix="/projects", tags=["Projects"])  # AJOUTÉ
    app.include_router(admin_router, prefix="/admin", tags=["Admin"])
    app.include_router(admin_users_router, prefix="/admin/users", tags=["Admin Users"])
    app.include_router(cours_router)  # AJOUTÉ: cours_router
    app.include_router(dashboard_router)  # AJOUTÉ: API Dashboard
    app.include_router(pdf_router)  # AJOUTÉ: API PDF
    app.include_router(public_test_router, prefix="/api/public", tags=["Public Test"])

    # ===================== TRANSLATIONS =====================
    translations = {
        "fr": {
            "nav_home": "Accueil",
            "nav_about": "À propos",
            "nav_portfolio": "Portfolio",
            "nav_contact": "Contact",
            "nav_messages": "Messages",
            "nav_login": "Connexion",
            "nav_register": "Inscription",
            "nav_logout": "Déconnexion",
            "nav_legal": "Mentions légales",
            "nav_privacy": "Politique de confidentialité",
            "cookies_banner": "Ce site utilise des cookies.",
            "cookies_accept": "Accepter",
            "cookies_decline": "Refuser",
            "home_title": "Bienvenue sur mon Portfolio 🚀",
            "contact_confirmation": "Message envoyé avec succès",
            "messages_title": "Messages reçus",
            "portfolio_title": "Mes projets",
            "publications_title": "Publications",
            "distinctions_title": "Distinctions",
            "academic_title": "Parcours académique"
        },
        "en": {
            "nav_home": "Home",
            "nav_about": "About",
            "nav_portfolio": "Portfolio",
            "nav_contact": "Contact",
            "nav_messages": "Messages",
            "nav_login": "Login",
            "nav_register": "Register",
            "nav_logout": "Logout",
            "nav_legal": "Legal notice",
            "nav_privacy": "Privacy policy",
            "cookies_banner": "This site uses cookies.",
            "cookies_accept": "Accept",
            "cookies_decline": "Decline",
            "home_title": "Welcome to my Portfolio 🚀",
            "contact_confirmation": "Message sent successfully",
            "messages_title": "Received messages",
            "portfolio_title": "My projects",
            "publications_title": "Publications",
            "distinctions_title": "Distinctions",
            "academic_title": "Academic career"
        }
    }

    def get_lang(request: Request):
        return request.session.get("lang", "fr")

    def base_context(request: Request, current_user: User | None = None):
        ctx = {
            "request": request,
            "t": translations[get_lang(request)],
            "lang": get_lang(request),
            "current_year": datetime.now().year,
            "now": datetime.now(),
            "cookies_accepted": request.session.get("cookies_accepted", False)
        }
        if current_user:
            ctx["username"] = current_user.email
            ctx["role"] = current_user.role
            ctx["is_admin"] = current_user.role in ["admin", "super_admin"]
        return ctx

    # ===================== PAGES PUBLIQUES =====================
    @app.get("/", response_class=HTMLResponse)
    def home(request: Request, current_user=Depends(get_current_user_optional)):
        ctx = base_context(request, current_user)
        ctx["page_title"] = ctx["t"]["home_title"]
        return templates.TemplateResponse(request, "home.html", ctx)

    @app.get("/about", response_class=HTMLResponse)
    def about(request: Request, current_user=Depends(get_current_user_optional)):
        ctx = base_context(request, current_user)
        ctx["page_title"] = ctx["t"]["nav_about"]
        return templates.TemplateResponse(request, "about.html", ctx)

    @app.get("/contact", response_class=HTMLResponse)
    def contact_page(request: Request, current_user=Depends(get_current_user_optional)):
        ctx = base_context(request, current_user)
        ctx["page_title"] = ctx["t"]["nav_contact"]
        return templates.TemplateResponse(request, "contact.html", ctx)

    @app.get("/legal", response_class=HTMLResponse)
    def legal(request: Request, current_user=Depends(get_current_user_optional)):
        ctx = base_context(request, current_user)
        ctx["page_title"] = ctx["t"]["nav_legal"]
        return templates.TemplateResponse(request, "legal.html", ctx)

    @app.get("/privacy", response_class=HTMLResponse)
    def privacy(request: Request, current_user=Depends(get_current_user_optional)):
        ctx = base_context(request, current_user)
        ctx["page_title"] = ctx["t"]["nav_privacy"]
        return templates.TemplateResponse(request, "privacy.html", ctx)

    # ===================== CONTACT =====================
    @app.post("/contact")
    def send_contact(
        request: Request,
        name: str = Form(...),
        email: str = Form(...),
        message: str = Form(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
        if not profile:
            raise HTTPException(status_code=400, detail="Profil non trouvé")

        new_message = MessageContact(
            profile_id=profile.id,
            sender_name=name,
            sender_email=email,
            message=message,
            created_at=datetime.utcnow()
        )
        db.add(new_message)

        audit = Audit(
            user_id=current_user.id,
            user_role=current_user.role,
            action_description=f"Message de contact envoyé par {email}",
            date=datetime.utcnow()
        )
        db.add(audit)

        db.commit()
        
        if "application/json" in request.headers.get("accept", ""):
            return {"message": "Message envoyé avec succès", "status": "success"}
        
        return RedirectResponse("/messages?sent=1", status_code=302)
    
    # ===================== LOGIN PAGE (GET) =====================
    @app.get("/login", response_class=HTMLResponse)
    def login_page(request: Request, current_user=Depends(get_current_user_optional)):
        """Page de connexion HTML"""
        # Si déjà connecté, rediriger
        if current_user:
            return RedirectResponse("/", status_code=302)
    
        ctx = base_context(request, current_user)
        ctx["page_title"] = "Connexion"
        return templates.TemplateResponse(request, "auth/login.html", ctx)

    # ===================== MESSAGES =====================
    @app.get("/messages", response_class=HTMLResponse)
    def messages_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
        profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profil non trouvé")
        
        messages = db.query(MessageContact).filter(
            MessageContact.profile_id == profile.id
        ).order_by(MessageContact.created_at.desc()).all()

        ctx = base_context(request, current_user)
        ctx["messages"] = messages
        ctx["page_title"] = ctx["t"]["messages_title"]
        ctx["message_sent"] = request.query_params.get("sent") == "1"
        return templates.TemplateResponse(request, "messages.html", ctx)

    # ===================== PORTFOLIO =====================
    @app.get("/portfolio", response_class=HTMLResponse)
    def portfolio_page(request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user_optional)):
        projects = db.query(Project).order_by(Project.year.desc()).all()
        
        # Formater les coauteurs pour le template
        for project in projects:
            if project.coauthor and isinstance(project.coauthor, list):
                project.coauthors_formatted = ", ".join(project.coauthor)
            else:
                project.coauthors_formatted = ""
            
            project.comments = db.query(Comment).filter(
                Comment.project_id == project.id
            ).order_by(Comment.created_at.desc()).all()
        
        ctx = base_context(request, current_user)
        ctx["projects"] = projects
        ctx["page_title"] = ctx["t"]["portfolio_title"]
        ctx["comment_success"] = request.query_params.get("success") == "1"
        return templates.TemplateResponse(request, "portfolio.html", ctx)

    @app.post("/portfolio/comment")
    def portfolio_comment(
        request: Request,
        project_id: int = Form(...),
        comment: str = Form(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
        
        new_comment = Comment(
            project_id=project_id,
            user_id=current_user.id,
            comment=comment,
            date=datetime.utcnow()
        )
        db.add(new_comment)

        audit = Audit(
            user_id=current_user.id,
            user_role=current_user.role,
            action_description=f"Commentaire ajouté sur le projet '{project.title}'",
            date=datetime.utcnow()
        )
        db.add(audit)

        db.commit()
        
        if "application/json" in request.headers.get("accept", ""):
            return {"message": "Commentaire ajouté", "status": "success", "comment_id": new_comment.id}
        
        return RedirectResponse(f"/portfolio?success=1&project={project_id}", status_code=302)

    # ===================== ACADEMIC CAREER =====================
    @app.get("/academic-career", response_class=HTMLResponse)
    def academic_career_page(request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user_optional)):
        academic_career = db.query(AcademicCareer).order_by(AcademicCareer.year.desc()).all()
        
        ctx = base_context(request, current_user)
        ctx["academic_career"] = academic_career
        ctx["page_title"] = ctx["t"]["academic_title"]
        return templates.TemplateResponse(request, "academic_career.html", ctx)

    # ===================== PUBLICATIONS =====================
    @app.get("/publications", response_class=HTMLResponse)
    def publications_page(request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user_optional)):
        try:
            # Essayer de récupérer les publications
            publications = db.query(Publication).order_by(Publication.year.desc()).all()
            
            # Formater les coauteurs pour le template
            for pub in publications:
                if pub.coauthor and isinstance(pub.coauthor, list):
                    pub.coauthors_formatted = ", ".join(pub.coauthor)
                else:
                    pub.coauthors_formatted = ""
            
        except Exception as e:
            # En cas d'erreur SQLAlchemy, retourner une liste vide et logger l'erreur
            print(f"⚠️  Erreur lors de la récupération des publications: {e}")
            publications = []
        
        ctx = base_context(request, current_user)
        ctx["publications"] = publications
        ctx["page_title"] = ctx["t"]["publications_title"]
        return templates.TemplateResponse(request, "publications.html", ctx)

    # ===================== DISTINCTIONS =====================
    @app.get("/distinctions", response_class=HTMLResponse)
    def distinctions_page(request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user_optional)):
        distinctions = db.query(Distinction).order_by(Distinction.year.desc()).all()
        
        ctx = base_context(request, current_user)
        ctx["distinctions"] = distinctions
        ctx["page_title"] = ctx["t"]["distinctions_title"]
        return templates.TemplateResponse(request, "distinctions.html", ctx)

    # ===================== COURS =====================
    @app.get("/cours", response_class=HTMLResponse)
    def cours_page(request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user_optional)):
        cours_list = db.query(Cours).order_by(Cours.id.desc()).all()
        
        ctx = base_context(request, current_user)
        ctx["cours"] = cours_list
        ctx["page_title"] = "Cours"
        return templates.TemplateResponse(request, "cours.html", ctx)

    # ===================== MEDIA ARTEFACTS =====================
    @app.get("/media", response_class=HTMLResponse)
    def media_page(request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user_optional)):
        media = db.query(MediaArtefact).order_by(MediaArtefact.created_at.desc()).all()
        
        ctx = base_context(request, current_user)
        ctx["media"] = media
        ctx["page_title"] = "Médias"
        return templates.TemplateResponse(request, "media.html", ctx)

    # ===================== AUDITS (ADMIN) =====================
    @app.get("/admin/audits")
    def get_audits(
        db: Session = Depends(get_db), 
        current_user: User = Depends(get_current_user),
        skip: int = 0,
        limit: int = 100
    ):
        if current_user.role not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Accès refusé")
        
        audits = db.query(Audit).order_by(Audit.date.desc()).offset(skip).limit(limit).all()
        total = db.query(Audit).count()
        
        return {
            "audits": audits,
            "total": total,
            "skip": skip,
            "limit": limit
        }

    # ===================== EXPORT AUDITS =====================
    @app.get("/admin/audits/export")
    def export_audits(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
        if current_user.role not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Accès refusé")

        audits = db.query(Audit).order_by(Audit.date.desc()).all()
        
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')
        
        writer.writerow(["ID", "Date", "User ID", "Role", "Action"])
        
        for audit in audits:
            writer.writerow([
                audit.id,
                audit.date.strftime("%Y-%m-%d %H:%M:%S") if audit.date else "N/A",
                audit.user_id,
                audit.user_role or "N/A",
                audit.action_description or "N/A"
            ])
        
        output.seek(0)
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            media_type="text/csv; charset=utf-8-sig",
            headers={
                "Content-Disposition": "attachment; filename=audits_export.csv",
                "Content-Type": "text/csv; charset=utf-8-sig"
            }
        )

    # ===================== DASHBOARD EXPORT CSV =====================
    @app.get("/admin/dashboard/export/csv")
    def export_dashboard_csv(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
        """Export CSV des statistiques dashboard - VERSION CORRIGÉE"""
        if current_user.role not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Accès refusé")
        
        try:
            user_count = db.query(User).count()
            audit_count = db.query(Audit).count()
            message_count = db.query(MessageContact).count()
            
            # Variables avec gestion d'erreur
            publication_count = 0
            project_count = 0
            cours_count = 0
            
            try:
                publication_count = db.query(Publication).count()
            except Exception as e:
                print(f"⚠️  Erreur comptage publications: {e}")
                
            try:
                project_count = db.query(Project).count()
            except Exception as e:
                print(f"⚠️  Erreur comptage projets: {e}")
                
            try:
                cours_count = db.query(Cours).count()
            except Exception as e:
                print(f"⚠️  Erreur comptage cours: {e}")
            
            output = io.StringIO()
            writer = csv.writer(output, delimiter=';')
            
            writer.writerow(["Statistique", "Valeur"])
            writer.writerow(["Nombre d'utilisateurs", user_count])
            writer.writerow(["Nombre d'audits", audit_count])
            writer.writerow(["Nombre de messages", message_count])
            writer.writerow(["Nombre de publications", publication_count])
            writer.writerow(["Nombre de projets", project_count])
            writer.writerow(["Nombre de cours", cours_count])
            writer.writerow([])
            writer.writerow(["Date d'export", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")])
            
            output.seek(0)
            
            return StreamingResponse(
                io.BytesIO(output.getvalue().encode('utf-8-sig')),
                media_type="text/csv; charset=utf-8-sig",
                headers={
                    "Content-Disposition": "attachment; filename=dashboard_stats.csv",
                    "Content-Type": "text/csv; charset=utf-8-sig"
                }
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Erreur export CSV: {str(e)[:200]}")

    # ===================== DASHBOARD EXPORT PDF (MOCK) =====================
    @app.get("/admin/dashboard/export/pdf")
    def export_dashboard_pdf(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
        if current_user.role not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Accès refusé")
        
        return {
            "message": "Export PDF à implémenter",
            "status": "not_implemented",
            "suggestion": "Utilisez /admin/dashboard/export/csv pour l'export CSV",
            "stats": {
                "user_count": db.query(User).count(),
                "audit_count": db.query(Audit).count(),
                "message_count": db.query(MessageContact).count()
            }
        }

    # ===================== AUDIT STATS =====================
    @app.get("/admin/audit-stats")
    def audit_stats(
        db: Session = Depends(get_db), 
        current_user: User = Depends(get_current_user),
        days: int = 30
    ):
        if current_user.role not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Accès refusé")

        start_date = datetime.utcnow().date() - timedelta(days=days)
        
        stats = db.query(
            func.date(Audit.date).label('date'),
            func.count(Audit.id).label('count')
        ).filter(
            Audit.date >= start_date
        ).group_by(
            func.date(Audit.date)
        ).order_by('date').all()
        
        result = []
        for stat in stats:
            if isinstance(stat.date, date):
                date_str = stat.date.isoformat()
            else:
                date_str = stat.date
                
            result.append({
                "date": date_str,
                "count": stat.count
            })
        
        return result

    # ===================== HEALTH CHECK =====================
    @app.get("/health")
    def health_check(db: Session = Depends(get_db)):
        """Health check - VERSION CORRIGÉE"""
        try:
            # CORRECTION: utiliser text() pour la requête SQL
            db.execute(text("SELECT 1"))
            db_status = "connected"
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": db_status,
            "version": "1.0.0"
        }

    # ===================== ERROR HANDLERS =====================
    @app.exception_handler(404)
    async def not_found_exception_handler(request: Request, exc: HTTPException):
        ctx = base_context(request, None)
        ctx["error_code"] = 404
        ctx["error_message"] = "Page non trouvée"
        return templates.TemplateResponse(request, "error.html", ctx, status_code=404)

    @app.exception_handler(429)
    async def rate_limit_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=429,
            content={
                "error": "Trop de requêtes",
                "message": "Limite de 100 requêtes par minute atteinte. Veuillez réessayer dans 60 secondes.",
                "retry_after": 60
            }
        )

    @app.exception_handler(500)
    async def internal_server_error_handler(request: Request, exc: HTTPException):
        ctx = base_context(request, None)
        ctx["error_code"] = 500
        ctx["error_message"] = "Erreur interne du serveur"
        return templates.TemplateResponse(request, "error.html", ctx, status_code=500)

    # ===================== LANGUE =====================
    @app.get("/lang/{lang_code}")
    def switch_lang(lang_code: str, request: Request):
        if lang_code in ["fr", "en"]:
            request.session["lang"] = lang_code
        
        referer = request.headers.get("referer", "/")
        return RedirectResponse(referer)

    # ===================== SITEMAP =====================
    @app.get("/sitemap.xml", include_in_schema=False)
    def sitemap():
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
        
        urls = [
            f"{base_url}/",
            f"{base_url}/about",
            f"{base_url}/portfolio",
            f"{base_url}/contact",
            f"{base_url}/publications",
            f"{base_url}/distinctions",
            f"{base_url}/academic-career",
            f"{base_url}/cours",
            f"{base_url}/media",
            f"{base_url}/legal",
            f"{base_url}/privacy"
        ]
        
        sitemap_content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
"""
        
        for url in urls:
            sitemap_content += f"""  <url>
    <loc>{url}</loc>
    <lastmod>{datetime.utcnow().strftime('%Y-%m-%d')}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
"""
        
        sitemap_content += "</urlset>"
        
        return Response(content=sitemap_content, media_type="application/xml")

    # ===================== FAVICON =====================
    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        return RedirectResponse(url="/static/favicon.ico")

    # ===================== COOKIES =====================
    @app.post("/cookies/accept")
    def accept_cookies(request: Request):
        request.session["cookies_accepted"] = True
        return {"status": "ok", "message": "Cookies acceptés"}

    @app.post("/cookies/decline")
    def decline_cookies(request: Request):
        request.session["cookies_accepted"] = False
        return {"status": "ok", "message": "Cookies refusés"}

    @app.get("/cookies/status")
    def cookies_status(request: Request):
        return {"accepted": request.session.get("cookies_accepted", False)}

    # ===================== API INFO =====================
    @app.get("/api/info")
    def api_info():
        return {
            "name": "Portfolio FastAPI",
            "version": "1.0.0",
            "description": "Application web portfolio bilingue avec authentification et audit",
            "author": "Votre Nom",
            "contact": "contact@example.com",
            "documentation": "/docs",
            "endpoints": {
                "public": [
                    "/", "/about", "/portfolio", "/contact", 
                    "/publications", "/distinctions", "/academic-career",
                    "/cours", "/media", "/legal", "/privacy"
                ],
                "auth": ["/auth/register", "/auth/login", "/auth/logout"],
                "admin": [
                    "/admin/audits", "/admin/audits/export",
                    "/admin/audit-stats", "/admin/dashboard/export/csv",
                    "/admin/dashboard/export/pdf"
                ],
                "api": ["/docs", "/redoc", "/openapi.json", "/health", "/api/info"]
            }
        }

    # ===================== SEARCH =====================
    @app.get("/search")
    def search(
        request: Request,
        q: str = "",
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user_optional)
    ):
        if not q:
            return {"results": []}
        
        results = []
        
        # Recherche dans les projets
        try:
            projects = db.query(Project).filter(
                Project.title.ilike(f"%{q}%")
            ).limit(10).all()
            for project in projects:
                results.append({
                    "type": "project",
                    "id": project.id,
                    "title": project.title,
                    "description": project.description[:100] + "..." if project.description and len(project.description) > 100 else project.description or "",
                    "url": f"/portfolio?highlight={project.id}"
                })
        except:
            pass
        
        # Recherche dans les publications
        try:
            publications = db.query(Publication).filter(
                Publication.title.ilike(f"%{q}%") | 
                Publication.journal.ilike(f"%{q}%")
            ).limit(10).all()
            for pub in publications:
                # Formater les coauteurs
                authors_str = ", ".join(pub.coauthor) if pub.coauthor and isinstance(pub.coauthor, list) else ""
                results.append({
                    "type": "publication",
                    "id": pub.id,
                    "title": pub.title,
                    "description": f"Auteurs: {authors_str} | Journal: {pub.journal or 'N/A'}",
                    "url": f"/publications?highlight={pub.id}"
                })
        except:
            pass
        
        # Recherche dans les cours
        try:
            cours = db.query(Cours).filter(
                Cours.title.ilike(f"%{q}%")
            ).limit(10).all()
            for c in cours:
                results.append({
                    "type": "cours",
                    "id": c.id,
                    "title": c.title,
                    "description": c.description[:100] + "..." if c.description and len(c.description) > 100 else c.description or "",
                    "url": f"/cours?highlight={c.id}"
                })
        except:
            pass
        
        return {"query": q, "count": len(results), "results": results}

    print("✅ Application FastAPI configurée avec succès!")

except Exception as e:
    print(f"❌ ERREUR CRITIQUE AU DÉMARRAGE: {e}")
    traceback.print_exc()
    
    # Créer une application minimaliste de secours
    from fastapi import FastAPI
    app = FastAPI()
    
    @app.get("/")
    def root():
        return {"error": "Application en mode secours", "message": str(e)}
    
    @app.get("/health")
    def health():
        return {"status": "degraded", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )