# routes/public_test.py - Routes publiques pour test
from fastapi import APIRouter
from fastapi.responses import Response

router = APIRouter()

@router.get("/dashboard-test")
def dashboard_test():
    """Route publique pour tester le dashboard"""
    return {
        "message": "Dashboard API fonctionne (public test)",
        "status": "success",
        "test_data": {
            "total_users": 150,
            "total_audits": 750,
            "total_messages": 120,
            "test": True
        }
    }

@router.get("/pdf-test")
def pdf_test():
    """Route publique pour tester le PDF"""
    fake_pdf = b"%PDF-1.4\nTest PDF - Dashboard Public Test\n"
    return Response(
        content=fake_pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=test_public.pdf"}
    )