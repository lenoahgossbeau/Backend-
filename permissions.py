from fastapi import Depends, HTTPException
from models.user import User
from auth.jwt import get_current_user

def require_role(*roles):
    """
    Vérifie que l'utilisateur connecté possède un rôle autorisé.
    Exemple :
        @router.get("/admin", dependencies=[Depends(require_role("admin", "super_admin"))])
    """
    def wrapper(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="Accès interdit ❌")
        return current_user
    return wrapper
