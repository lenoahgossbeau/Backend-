from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import random
from database import get_db
from models.user import User
from auth.jwt import get_current_user

router = APIRouter(prefix="/payment", tags=["Payment"])

class PaymentRequest(BaseModel):
    operator: str   # "orange" ou "mtn"
    phone: str
    amount: float

@router.post("/initiate")
def initiate_payment(
    payment: PaymentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Validation de l'opérateur
    if payment.operator not in ["orange", "mtn"]:
        raise HTTPException(status_code=400, detail="Opérateur invalide. Choisissez 'orange' ou 'mtn'.")

    # 2. Validation simple du numéro de téléphone (Cameroun)
    if not payment.phone.startswith("6") or len(payment.phone) != 9:
        raise HTTPException(status_code=400, detail="Numéro de téléphone invalide (ex: 612345678).")

    # 3. Simulation d'un paiement réussi (toujours vrai ici)
    # En production : appel à l'API Orange Money / MTN Money ou Strapile
    transaction_id = f"SIM_{current_user.id}_{random.randint(100000, 999999)}"

    return {
        "success": True,
        "transaction_id": transaction_id,
        "message": f"✅ Paiement de {payment.amount} XAF simulé avec succès via {payment.operator.upper()} Money.",
        "operator": payment.operator,
        "phone": payment.phone
    }