# ===================== ENV =====================
from dotenv import load_dotenv
load_dotenv()  # ⚠️ DOIT ÊTRE TOUT EN HAUT

import traceback
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="starlette")
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
    from sqlalchemy import func, text
    from datetime import datetime, date, timedelta, timezone
    import io, csv, os, time, sys
    from collections import defaultdict

    # ===================== DATABASE =====================
    from database import get_db
    from init_db import init_db

    # ===================== MODELS =====================
    from database import Base

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
    from routes.contact import router as contact_router
    from auth.router import router as auth_router
    from routes.admin import admin_router
    from routes.admin_users import admin_users_router
    from routes.cours import router as cours_router
    from routes.dashboard import router as dashboard_router
    from routes.pdf import router as pdf_router
    from routes.project import router as project_router
    from routes.admin_subscriptions import router as admin_subscriptions_router
    from routes.cv import router as cv_router
    from routes.activation import router as activation_router
    from routes.admin_activation import router as admin_activation_router
    from routes.researcher_messages import router as researcher_messages_router
    from routes.researcher_public import router as researcher_public_router
    from routes.payment import router as payment_router
    from routes.admin_audit import router as admin_audit_router

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
        openapi_schema["security"] = [{"BearerAuth": []}]
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    # ===================== CORS =====================
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:3002",
            "http://localhost:3003",
            "http://127.0.0.1:3000",
            "http://jean-dupont.localhost:3000",  # 👈 AJOUT ICI
            "https://portfolio-frontend-jlq1.onrender.com",
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept"],
    )

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

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Process-Time"] = str(process_time)

        if request.url.scheme == "https" and not TEST_MODE:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        if request.url.path.startswith("/api/"):
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"

        return response

    # ===================== RATE LIMIT =====================
    RATE_LIMIT = 100
    WINDOW = 60
    requests_counter = defaultdict(list)

    @app.get("/test/reset-rate-limiter")
    def reset_rate_limiter():
        """Réinitialise le rate limiter pour les tests"""
        requests_counter.clear()
        return {"message": "Rate limiter réinitialisé"}

    @app.middleware("http")
    async def rate_limiter(request: Request, call_next):
        public_paths = [
            "/", "/about", "/contact", "/legal", "/privacy",
            "/portfolio", "/publications", "/distinctions",
            "/academic-career", "/cours", "/media",
            "/health", "/docs", "/redoc", "/openapi.json",
            "/sitemap.xml", "/favicon.ico", "/api/info",
            "/test/reset-rate-limiter"
        ]

        if request.url.path in public_paths:
            return await call_next(request)

        ip = request.headers.get("X-Forwarded-For", request.client.host)
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
                headers={
                    "Retry-After": str(WINDOW),
                    "X-RateLimit-Limit": str(RATE_LIMIT),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(now + WINDOW))
                }
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
    app.include_router(auth_router)
    app.include_router(user_router, prefix="/users", tags=["Users"])
    app.include_router(profile_router, tags=["Profiles"])
    app.include_router(publication_router, prefix="/publications", tags=["Publications"])
    app.include_router(project_router, prefix="/projects", tags=["Projects"])
    app.include_router(admin_router)
    app.include_router(admin_users_router, tags=["Admin Users"])
    app.include_router(cours_router)
    app.include_router(dashboard_router)
    app.include_router(pdf_router)
    app.include_router(public_test_router, prefix="/api/public", tags=["Public Test"])
    app.include_router(admin_subscriptions_router)
    app.include_router(activation_router)
    app.include_router(admin_activation_router)
    app.include_router(researcher_public_router)
    app.include_router(researcher_messages_router)
    app.include_router(payment_router)
    app.include_router(admin_audit_router)
    print("🔧 Chargement du routeur CV...")
    app.include_router(cv_router)
    app.include_router(contact_router)
    print("✅ Routeur CV chargé")

    # ===================== ROUTES DE TEST POUR LE RATE LIMITER =====================
    @app.get("/api/test-rate-limiter")
    @app.get("/api/test-rate-limiter-{suffix}")
    async def test_rate_limiter_route():
        return {"message": "Route de test"}

    @app.get("/api/test-error-message")
    @app.get("/api/test-error-message-{suffix}")
    async def test_error_message_route():
        return {"message": "Route de test"}

    @app.get("/api/test-headers")
    async def test_headers_route():
        return {"message": "Route de test"}

    @app.get("/api/test1-{suffix}")
    @app.get("/api/test2-{suffix}")
    @app.get("/api/test3-{suffix}")
    @app.get("/api/test4-{suffix}")
    async def test_shared_counter_routes():
        return {"message": "Route de test"}

    @app.get("/api/extra-{suffix}")
    async def test_extra_route():
        return {"message": "Route de test"}

    @app.get("/api/final-test")
    async def test_final_route():
        return {"message": "Route de test"}

    @app.get("/api/test-reset")
    @app.get("/api/test-reset-{suffix}")
    async def test_reset_route():
        return {"message": "Route de test"}

    @app.get("/api/test-ip")
    @app.get("/api/test-ip-{suffix}")
    @app.get("/api/test-ip-ip2-{suffix}")
    @app.get("/api/test-ip-ip1-extra-{suffix}")
    @app.get("/api/test-ip-ip1-final")
    @app.get("/api/test-ip-ip2-extra-{suffix}")
    async def test_ip_route():
        return {"message": "Route de test"}

    @app.get("/admin/final-test")
    async def test_admin_final_route():
        return {"message": "Route de test admin"}

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

    # ===================== PING =====================
    @app.get("/ping")
    def ping():
        return {"message": "pong"}

    # ===================== RESEARCHER PUBLIC PROFILE =====================
    @app.get("/researcher/public/{user_id}")
    def get_public_researcher_profile(user_id: int, db: Session = Depends(get_db)):
        user = db.query(User).filter(
            User.id == user_id,
            User.role == "researcher"
        ).first()

        if not user:
            return {"error": "Chercheur non trouvé"}

        profile = db.query(Profile).filter(
            Profile.user_id == user.id
        ).first()

        publications = []
        projects = []

        if profile:
            publications = db.query(Publication).filter(
                Publication.profile_id == profile.id
            ).all()

            projects = db.query(Project).filter(
                Project.profile_id == profile.id
            ).all()

        return {
            "id": user.id,
            "email": user.email,
            "firstName": profile.first_name if profile else "",
            "lastName": profile.last_name if profile else "",
            "profession": profile.grade if profile else "",
            "bio": profile.bio if profile else "",
            "publications": [
                {
                    "id": p.id,
                    "title": p.title,
                    "year": p.year,
                    "coauthor": p.coauthor
                }
                for p in publications
            ],
            "projects": [
                {
                    "id": p.id,
                    "title": p.title,
                    "year": p.year,
                    "description": p.description
                }
                for p in projects
            ]
        }

    # ===================== RESEARCHERS LIST =====================
    @app.get("/researchers")
    def list_researchers(db: Session = Depends(get_db)):
        # ✅ CORRECTION: status == "active" au lieu de is_active == True
        researchers = db.query(User).filter(
            User.role == "researcher",
            User.status == "active"
        ).all()

        result = []
        for r in researchers:
            profile = db.query(Profile).filter(Profile.user_id == r.id).first()
            result.append({
                "id": r.id,
                "email": r.email,
                "firstName": profile.first_name if profile and profile.first_name else "",
                "lastName": profile.last_name if profile and profile.last_name else "",
            })
        # ✅ CORRECTION: return en dehors de la boucle for
        return result

    # ===================== PAGES PUBLIQUES =====================
    @app.get("/", response_class=HTMLResponse)
    def home(request: Request, current_user=Depends(get_current_user_optional)):
        ctx = base_context(request, current_user)
        ctx["page_title"] = ctx["t"]["home_title"]
        return templates.TemplateResponse("home.html", ctx)

    @app.get("/about", response_class=HTMLResponse)
    def about(request: Request, current_user=Depends(get_current_user_optional)):
        ctx = base_context(request, current_user)
        ctx["page_title"] = ctx["t"]["nav_about"]
        return templates.TemplateResponse("about.html", ctx)

    @app.get("/contact", response_class=HTMLResponse)
    def contact_page(request: Request, current_user=Depends(get_current_user_optional)):
        ctx = base_context(request, current_user)
        ctx["page_title"] = ctx["t"]["nav_contact"]
        return templates.TemplateResponse("contact.html", ctx)

    @app.get("/legal", response_class=HTMLResponse)
    def legal(request: Request, current_user=Depends(get_current_user_optional)):
        ctx = base_context(request, current_user)
        ctx["page_title"] = ctx["t"]["nav_legal"]
        return templates.TemplateResponse("legal.html", ctx)

    @app.get("/privacy", response_class=HTMLResponse)
    def privacy(request: Request, current_user=Depends(get_current_user_optional)):
        ctx = base_context(request, current_user)
        ctx["page_title"] = ctx["t"]["nav_privacy"]
        return templates.TemplateResponse("privacy.html", ctx)

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
            created_at=datetime.now(timezone.utc)
        )
        db.add(new_message)

        audit = Audit(
            user_id=current_user.id,
            user_role=current_user.role,
            action_description=f"Message de contact envoyé par {email}",
        )
        db.add(audit)
        db.commit()

        if "application/json" in request.headers.get("accept", ""):
            return {"message": "Message envoyé avec succès", "status": "success"}

        return RedirectResponse("/messages?sent=1", status_code=302)

    # ===================== CONTACT API (PUBLIC) =====================
    @app.post("/api/contact")
    async def send_contact_public(
        request: Request,
        db: Session = Depends(get_db)
    ):
        try:
            data = await request.json()
            name = data.get("name")
            email = data.get("email")
            message = data.get("message")

            if not name or not email or not message:
                return JSONResponse(
                    status_code=400,
                    content={"error": "Tous les champs sont requis"}
                )

            new_message = MessageContact(
                profile_id=None,
                sender_name=name,
                sender_email=email,
                message=message,
                created_at=datetime.now(timezone.utc)
            )
            db.add(new_message)
            db.commit()

            return {"message": "Message envoyé avec succès", "status": "success"}

        except Exception as e:
            print(f"Erreur détaillée: {e}")
            traceback.print_exc()
            return JSONResponse(
                status_code=500,
                content={"error": f"Erreur lors de l'envoi: {str(e)}"}
            )

    # ===================== LOGIN PAGE (GET) =====================
    @app.get("/login", response_class=HTMLResponse)
    def login_page(request: Request, current_user=Depends(get_current_user_optional)):
        if current_user:
            return RedirectResponse("/", status_code=302)
        ctx = base_context(request, current_user)
        ctx["page_title"] = "Connexion"
        return templates.TemplateResponse("auth/login.html", ctx)

    # ===================== LOGIN API (POST) - Compatibilité =====================
    @app.post("/login")
    async def login_compat(request: Request, db: Session = Depends(get_db)):
        try:
            if request.headers.get("content-type") == "application/json":
                data = await request.json()
                email = data.get("email")
                password = data.get("password")
            else:
                form = await request.form()
                email = form.get("email")
                password = form.get("password")

            if not email or not password:
                return JSONResponse(status_code=400, content={"detail": "Email et mot de passe requis"})

            from auth.jwt import create_access_token, create_refresh_token
            from auth.security import verify_password
            from models.refresh_token import RefreshToken

            user = db.query(User).filter(User.email == email).first()

            if not user or not verify_password(password, user.password):
                audit = Audit(
                    user_id=user.id if user else None,
                    user_role=user.role if user else 'unknown',
                    action_description=f"Tentative de login échouée pour {email}"
                )
                db.add(audit)
                db.commit()
                return JSONResponse(status_code=401, content={"detail": "Email ou mot de passe incorrect"})

            if user.status != "active":
                return JSONResponse(status_code=403, content={"detail": "Compte inactif"})

            access_token = create_access_token(user_id=user.id, role=user.role, expires_delta=timedelta(minutes=15))
            refresh_token = create_refresh_token(user_id=user.id, role=user.role, expires_delta=timedelta(days=7))

            db_refresh = RefreshToken(user_id=user.id, token=refresh_token, revoked=False)
            db.add(db_refresh)

            audit = Audit(
                user_id=user.id,
                user_role=user.role,
                action_description="Login réussi via endpoint /login (compatibilité)"
            )
            db.add(audit)
            db.commit()

            response = JSONResponse(content={
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "user": {"id": user.id, "email": user.email, "role": user.role}
            })
            response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, max_age=7*24*60*60, secure=False, samesite="lax")
            response.set_cookie(key="access_token", value=access_token, httponly=True, max_age=15*60, secure=False, samesite="lax")
            return response

        except Exception as e:
            traceback.print_exc()
            return JSONResponse(status_code=500, content={"detail": f"Erreur interne: {str(e)}"})

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
        return templates.TemplateResponse("messages.html", ctx)

    # ===================== PORTFOLIO =====================
    @app.get("/portfolio", response_class=HTMLResponse)
    def portfolio_page(request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user_optional)):
        projects = db.query(Project).order_by(Project.year.desc()).all()
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
        return templates.TemplateResponse("portfolio.html", ctx)

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
            date=datetime.now(timezone.utc)
        )
        db.add(new_comment)

        audit = Audit(
            user_id=current_user.id,
            user_role=current_user.role,
            action_description=f"Commentaire ajouté sur le projet '{project.title}'",
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
        return templates.TemplateResponse("academic_career.html", ctx)

    # ===================== PUBLICATIONS =====================
    @app.get("/publications", response_class=HTMLResponse)
    def publications_page(request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user_optional)):
        try:
            publications = db.query(Publication).order_by(Publication.year.desc()).all()
            for pub in publications:
                if pub.coauthor and isinstance(pub.coauthor, list):
                    pub.coauthors_formatted = ", ".join(pub.coauthor)
                else:
                    pub.coauthors_formatted = ""
        except Exception as e:
            print(f"⚠️  Erreur lors de la récupération des publications: {e}")
            publications = []

        ctx = base_context(request, current_user)
        ctx["publications"] = publications
        ctx["page_title"] = ctx["t"]["publications_title"]
        return templates.TemplateResponse("publications.html", ctx)

    # ===================== DISTINCTIONS =====================
    @app.get("/distinctions", response_class=HTMLResponse)
    def distinctions_page(request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user_optional)):
        distinctions = db.query(Distinction).order_by(Distinction.year.desc()).all()
        ctx = base_context(request, current_user)
        ctx["distinctions"] = distinctions
        ctx["page_title"] = ctx["t"]["distinctions_title"]
        return templates.TemplateResponse("distinctions.html", ctx)

    # ===================== COURS =====================
    @app.get("/cours", response_class=HTMLResponse)
    def cours_page(request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user_optional)):
        cours_list = db.query(Cours).order_by(Cours.id.desc()).all()
        ctx = base_context(request, current_user)
        ctx["cours"] = cours_list
        ctx["page_title"] = "Cours"
        return templates.TemplateResponse("cours.html", ctx)

    # ===================== MEDIA ARTEFACTS =====================
    @app.get("/media", response_class=HTMLResponse)
    def media_page(request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user_optional)):
        media = db.query(MediaArtefact).order_by(MediaArtefact.created_at.desc()).all()
        ctx = base_context(request, current_user)
        ctx["media"] = media
        ctx["page_title"] = "Médias"
        return templates.TemplateResponse("media.html", ctx)

    # ===================== HEALTH CHECK =====================
    @app.get("/health")
    def health_check(db: Session = Depends(get_db)):
        try:
            db.execute(text("SELECT 1"))
            db_status = "connected"
        except Exception as e:
            db_status = f"error: {str(e)}"

        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": db_status,
            "version": "1.0.0"
        }

    # ===================== ERROR HANDLERS =====================
    @app.exception_handler(404)
    async def not_found_exception_handler(request: Request, exc: HTTPException):
        ctx = base_context(request, None)
        ctx["error_code"] = 404
        ctx["error_message"] = "Page non trouvée"
        return templates.TemplateResponse("error.html", ctx, status_code=404)

    @app.exception_handler(429)
    async def rate_limit_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=429,
            content={
                "error": "Trop de requêtes",
                "message": "Limite de 100 requêtes par minute atteinte.",
                "retry_after": 60
            }
        )

    @app.exception_handler(500)
    async def internal_server_error_handler(request: Request, exc: HTTPException):
        ctx = base_context(request, None)
        ctx["error_code"] = 500
        ctx["error_message"] = "Erreur interne du serveur"
        return templates.TemplateResponse("error.html", ctx, status_code=500)

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
            f"{base_url}/", f"{base_url}/about", f"{base_url}/portfolio",
            f"{base_url}/contact", f"{base_url}/publications", f"{base_url}/distinctions",
            f"{base_url}/academic-career", f"{base_url}/cours", f"{base_url}/media",
            f"{base_url}/legal", f"{base_url}/privacy"
        ]
        sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        for url in urls:
            sitemap_content += f'  <url>\n    <loc>{url}</loc>\n    <lastmod>{datetime.now(timezone.utc).strftime("%Y-%m-%d")}</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>0.8</priority>\n  </url>\n'
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
            "endpoints": {
                "public": ["/", "/about", "/portfolio", "/contact", "/publications",
                           "/distinctions", "/academic-career", "/cours", "/media", "/legal", "/privacy"],
                "auth": ["/auth/register", "/auth/login", "/auth/logout", "/auth/refresh"],
                "admin": ["/admin/sessions", "/admin/audit-stats", "/admin/dashboard",
                          "/admin/dashboard/export/csv", "/admin/dashboard/export/pdf"],
                "api": ["/docs", "/redoc", "/openapi.json", "/health", "/api/info"]
            }
        }

    # ===================== SEARCH =====================
    @app.get("/search")
    def search(request: Request, q: str = "", db: Session = Depends(get_db), current_user=Depends(get_current_user_optional)):
        if not q:
            return {"results": []}

        results = []

        try:
            projects = db.query(Project).filter(Project.title.ilike(f"%{q}%")).limit(10).all()
            for project in projects:
                results.append({
                    "type": "project", "id": project.id, "title": project.title,
                    "description": (project.description[:100] + "...") if project.description and len(project.description) > 100 else (project.description or ""),
                    "url": f"/portfolio?highlight={project.id}"
                })
        except:
            pass

        try:
            publications = db.query(Publication).filter(
                Publication.title.ilike(f"%{q}%") | Publication.journal.ilike(f"%{q}%")
            ).limit(10).all()
            for pub in publications:
                authors_str = ", ".join(pub.coauthor) if pub.coauthor and isinstance(pub.coauthor, list) else ""
                results.append({
                    "type": "publication", "id": pub.id, "title": pub.title,
                    "description": f"Auteurs: {authors_str} | Journal: {pub.journal or 'N/A'}",
                    "url": f"/publications?highlight={pub.id}"
                })
        except:
            pass

        try:
            cours = db.query(Cours).filter(Cours.title.ilike(f"%{q}%")).limit(10).all()
            for c in cours:
                results.append({
                    "type": "cours", "id": c.id, "title": c.title,
                    "description": (c.description[:100] + "...") if c.description and len(c.description) > 100 else (c.description or ""),
                    "url": f"/cours?highlight={c.id}"
                })
        except:
            pass

        return {"query": q, "count": len(results), "results": results}

    # ===================== INIT DB (for Render) =====================
    @app.post("/admin/init-db")
    def init_database(db: Session = Depends(get_db)):
        try:
            from auth.security import hash_password
            from models.user import User
            from database import Base, engine

            Base.metadata.create_all(bind=engine)

            admin = db.query(User).filter(User.email == 'admin@test.com').first()
            if not admin:
                admin = User(
                    email='admin@test.com',
                    password=hash_password('admin123'),
                    role='admin',
                    status='active'
                )
                db.add(admin)
                db.commit()
                return {"message": "Base initialisée avec succès", "admin_created": True}
            else:
                return {"message": "Base déjà initialisée", "admin_exists": True}
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": str(e)})

    # ===================== INIT CV TABLES (for Render) =====================
    @app.post("/admin/init-cv-tables")
    def create_cv_tables():
        try:
            from models.cv import Base
            from database import engine
            Base.metadata.create_all(bind=engine)
            return {"message": "Tables CV créées avec succès"}
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": str(e)})

    print("✅ Application FastAPI configurée avec succès!")

except Exception as e:
    print(f"❌ ERREUR CRITIQUE AU DÉMARRAGE: {e}")
    traceback.print_exc()

    from fastapi import FastAPI
    app = FastAPI()

    @app.get("/ping")
    def ping_fallback():
        return {"message": "pong", "mode": "secours", "error": str(e)}

    @app.get("/health")
    def health_fallback():
        return {"status": "degraded", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")