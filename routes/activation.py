from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from database import get_db
from models.user import User
from auth.jwt import SECRET_KEY, ALGORITHM

router = APIRouter(
    prefix="/auth",
    tags=["Activation"]
)


@router.get("/activate")
def activate_account(
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    try:
        # Décodage du token
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        email = payload.get("sub")
        token_type = payload.get("type")

        # Vérification du type du token
        if not email:
            raise HTTPException(
                status_code=400,
                detail="Email introuvable dans le token"
            )

        if token_type != "activation":
            raise HTTPException(
                status_code=400,
                detail="Token invalide pour activation"
            )

    except JWTError:
        raise HTTPException(
            status_code=400,
            detail="Token invalide ou expiré"
        )

    # Recherche utilisateur
    user = db.query(User).filter(
        User.email == email
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Utilisateur non trouvé"
        )

    # Si déjà activé
    if user.is_active and user.status == "active":
        return {
            "message": "Compte déjà activé"
        }

    # Activation complète du compte
    user.is_active = True
    user.status = "active"

    db.commit()
    db.refresh(user)

    return {
        "message": "Compte activé avec succès",
        "email": user.email,
        "status": user.status
    }