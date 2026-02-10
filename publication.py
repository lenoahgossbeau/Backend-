from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.publication import Publication
from models.comment import Comment
from models.audit import Audit
from models.user import User
from schemas.publication import PublicationCreate, PublicationOut, PublicationUpdate
from schemas.comment import CommentCreate, CommentOut
from auth.dependencies import get_current_user

router = APIRouter(
    prefix="/publications",
    tags=["Publications"]
)

# ================== CRÉER UNE PUBLICATION ==================
@router.post("/", response_model=PublicationOut, summary="Créer une publication", description="Permet à un utilisateur connecté de créer une nouvelle publication.")
def create_publication(pub: PublicationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_pub = Publication(**pub.dict(exclude={"user_id"}), user_id=current_user.id)
    db.add(new_pub)
    db.commit()
    db.refresh(new_pub)

    audit_log = Audit(
        user_id=current_user.id,
        user_role=current_user.role,
        action_description=f"Publication créée: {new_pub.title}"
    )
    db.add(audit_log)
    db.commit()

    return new_pub

# ================== LISTER TOUTES LES PUBLICATIONS ==================
@router.get("/", response_model=list[PublicationOut], summary="Lister les publications", description="Retourne toutes les publications disponibles.")
def get_publications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Publication).all()

# ================== LIRE UNE PUBLICATION ==================
@router.get("/{pub_id}", response_model=PublicationOut, summary="Lire une publication", description="Retourne une publication par son identifiant.")
def get_publication(pub_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    pub = db.query(Publication).filter(Publication.id == pub_id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publication non trouvée ❌")
    return pub

# ================== METTRE À JOUR UNE PUBLICATION ==================
@router.put("/{pub_id}", response_model=PublicationOut, summary="Mettre à jour une publication", description="Permet à un utilisateur de modifier sa propre publication.")
def update_publication(pub_id: int, data: PublicationUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    pub = db.query(Publication).filter(Publication.id == pub_id, Publication.user_id == current_user.id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publication introuvable ou non autorisée ❌")
    for key, value in data.dict(exclude_unset=True).items():
        setattr(pub, key, value)
    db.commit()
    db.refresh(pub)

    audit_log = Audit(
        user_id=current_user.id,
        user_role=current_user.role,
        action_description=f"Publication mise à jour: {pub.title}"
    )
    db.add(audit_log)
    db.commit()

    return pub

# ================== SUPPRIMER UNE PUBLICATION ==================
@router.delete("/{pub_id}", summary="Supprimer une publication", description="Permet à un utilisateur de supprimer sa propre publication.")
def delete_publication(pub_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    pub = db.query(Publication).filter(Publication.id == pub_id, Publication.user_id == current_user.id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publication introuvable ou non autorisée ❌")
    db.delete(pub)
    db.commit()

    audit_log = Audit(
        user_id=current_user.id,
        user_role=current_user.role,
        action_description=f"Publication supprimée: {pub.title}"
    )
    db.add(audit_log)
    db.commit()

    return {"message": "Publication supprimée ✅"}

# ================== AJOUTER UN COMMENTAIRE ==================
@router.post("/{pub_id}/comments", response_model=CommentOut, summary="Ajouter un commentaire", description="Permet à un utilisateur connecté d'ajouter un commentaire sur une publication.")
def add_comment(pub_id: int, comment: CommentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    pub = db.query(Publication).filter(Publication.id == pub_id).first()
    if not pub:
        raise HTTPException(status_code=404, detail="Publication introuvable ❌")

    new_comment = Comment(content=comment.content, publication_id=pub_id, user_id=current_user.id)
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    audit_log = Audit(
        user_id=current_user.id,
        user_role=current_user.role,
        action_description=f"Commentaire ajouté sur publication {pub_id}"
    )
    db.add(audit_log)
    db.commit()

    return new_comment

# ================== LISTER LES COMMENTAIRES D’UNE PUBLICATION ==================
@router.get("/{pub_id}/comments", response_model=list[CommentOut], summary="Lister les commentaires", description="Retourne tous les commentaires associés à une publication.")
def get_comments(pub_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Comment).filter(Comment.publication_id == pub_id).all()

# ================== SUPPRIMER UN COMMENTAIRE ==================
@router.delete("/comments/{comment_id}", summary="Supprimer un commentaire", description="Permet à un utilisateur de supprimer son propre commentaire.")
def delete_comment(comment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.user_id == current_user.id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Commentaire introuvable ou non autorisé ❌")
    db.delete(comment)
    db.commit()

    audit_log = Audit(
        user_id=current_user.id,
        user_role=current_user.role,
        action_description=f"Commentaire supprimé (id={comment_id})"
    )
    db.add(audit_log)
    db.commit()

    return {"message": "Commentaire supprimé ✅"}
