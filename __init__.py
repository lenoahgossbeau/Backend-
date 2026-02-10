"""
Package models - Force l'import de tous les modèles
"""
# Import forcé de tous les modèles pour éviter les erreurs SQLAlchemy
from .user import User
from .profile import Profile
from .publication import Publication
from .project import Project
from .academic_career import AcademicCareer
from .distinction import Distinction
from .cours import Cours
from .media_artefact import MediaArtefact
from .comment import Comment
from .message_contact import MessageContact
from .audit import Audit
from .subscription import Subscription
from .refresh_token import RefreshToken

__all__ = [
    'User',
    'Profile', 
    'Publication',
    'Project',
    'AcademicCareer',
    'Distinction',
    'Cours',
    'MediaArtefact',
    'Comment',
    'MessageContact',
    'Audit',
    'Subscription',
    'RefreshToken'
]