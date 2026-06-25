import pytest
from datetime import datetime
import json

def test_user_model(db):
    """Test création d'utilisateur - CORRECTION SQLAlchemy"""
    from models.user import User
    from auth.security import hash_password
    
    user = User(
        email="model@example.com",
        password=hash_password("test"),
        role="user",
        status="active"
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    assert user.id is not None
    assert user.email == "model@example.com"
    assert user.role == "user"
    assert user.status == "active"
    
    # Test des relations
    assert hasattr(user, 'profile')
    assert hasattr(user, 'audits')
    
    print("✅ Test User model: PASSED")

def test_profile_model(db):
    """Test création de profil"""
    from models.user import User
    from models.profile import Profile
    from auth.security import hash_password
    
    # Créer un utilisateur
    user = User(
        email="profile@example.com",
        password=hash_password("test"),
        role="user",
        status="active"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Créer un profil
    profile = Profile(
        user_id=user.id,
        grade="Professeur",
        specialite="Informatique"
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    assert profile.id is not None
    assert profile.user_id == user.id
    assert profile.grade == "Professeur"
    assert profile.specialite == "Informatique"
    
    print("✅ Test Profile model: PASSED")

def test_publication_model_conforme(db):
    """Test création de publication CONFORME"""
    from models.user import User
    from models.profile import Profile
    from models.publication import Publication
    from auth.security import hash_password
    
    # Créer user et profile
    user = User(
        email="pubtest@example.com",
        password=hash_password("test"),
        role="researcher",
        status="active"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    profile = Profile(
        user_id=user.id,
        grade="Docteur",
        specialite="Physique"
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    # Publication CONFORME
    publication = Publication(
        profile_id=profile.id,
        year=2024,
        title="Test Publication Conforme",
        coauthor=["Dr. Smith", "Prof. Johnson"],  # Liste JSON
        journal="Nature",
        doi="10.1000/test"
    )
    db.add(publication)
    db.commit()
    db.refresh(publication)
    
    # VÉRIFICATIONS
    assert publication.id is not None
    assert publication.year == 2024  # ✅ year au lieu de date
    assert publication.title == "Test Publication Conforme"
    assert publication.coauthor == ["Dr. Smith", "Prof. Johnson"]
    assert isinstance(publication.coauthor, list)  # ✅ type list
    
    # ✅ Vérifier absence des anciens champs
    assert not hasattr(publication, 'abstract'), "❌ 'abstract' ne doit pas exister"
    assert not hasattr(publication, 'description'), "❌ 'description' ne doit pas exister"
    assert not hasattr(publication, 'date'), "❌ 'date' doit être remplacé par 'year'"
    
    print("✅ Test Publication model: PASSED (100% conforme)")

def test_project_model_conforme(db):
    """Test création de projet CONFORME"""
    from models.user import User
    from models.profile import Profile
    from models.project import Project
    from auth.security import hash_password
    
    # Créer user et profile
    user = User(
        email="projecttest@example.com",
        password=hash_password("test"),
        role="researcher",
        status="active"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    profile = Profile(
        user_id=user.id,
        grade="Ingénieur",
        specialite="Data Science"
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    # Project de base
    project = Project(
        profile_id=profile.id,
        year=2023,
        title="AI Research Project",
        coauthor=["Lab A", "Lab B"]
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    
    assert project.year == 2023  # ✅ year
    assert project.title == "AI Research Project"
    assert project.coauthor == ["Lab A", "Lab B"]
    
    print("✅ Test Project model: PASSED (conforme)")

def test_academic_career_model(db):
    """Test AcademicCareer"""
    from models.academic_career import AcademicCareer
    from models.user import User
    from models.profile import Profile
    from auth.security import hash_password
    
    user = User(
        email="career@example.com",
        password=hash_password("test"),
        role="researcher",
        status="active"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    profile = Profile(
        user_id=user.id,
        grade="Doctorant",
        specialite="Biologie"
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    career = AcademicCareer(
        profile_id=profile.id,
        year=2020,
        title_formation="Master en Biologie Moléculaire",  # ✅ title_formation
        diplome="Master",
        description="Formation approfondie"
    )
    db.add(career)
    db.commit()
    db.refresh(career)
    
    assert career.title_formation == "Master en Biologie Moléculaire"
    assert career.year == 2020
    assert career.diplome == "Master"
    
    print("✅ Test AcademicCareer: PASSED")

def test_relations_profile(db):
    """Test que Profile a les relations 1→N"""
    from models.profile import Profile
    from models.user import User
    from auth.security import hash_password
    
    user = User(
        email="relations@example.com",
        password=hash_password("test"),
        role="researcher",
        status="active"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    profile = Profile(
        user_id=user.id,
        grade="Chercheur",
        specialite="Chimie"
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    # Vérifier les relations
    relations = ['publications', 'projects', 'distinctions', 
                'academic_careers', 'cours', 'media_artefacts']
    
    for relation in relations:
        assert hasattr(profile, relation), f"Profile doit avoir {relation}"
    
    print("✅ Test relations Profile: PASSED")

def test_conformite_champs_json(db):
    """Test que coauthor est bien JSON/list"""
    from models.publication import Publication
    from models.project import Project
    
    # Test Publication
    pub = Publication(
        year=2024,
        title="Test JSON",
        coauthor=["Auteur 1", "Auteur 2"],
        profile_id=1
    )
    
    assert isinstance(pub.coauthor, list), "coauthor doit être une liste"
    assert len(pub.coauthor) == 2
    
    # Test Project
    proj = Project(
        year=2023,
        title="Test Project JSON",
        coauthor=["Équipe 1"],
        profile_id=1
    )
    
    assert isinstance(proj.coauthor, list)
    
    print("✅ Test champs JSON: PASSED")

def test_conformite_complete():
    """Test complet de conformité - VERSION CORRIGÉE SANS RETURN"""
    print("\n" + "="*60)
    print("TEST COMPLET DE CONFORMITÉ AU CAHIER DES CHARGES")
    print("="*60)
    
    from models.publication import Publication
    from models.project import Project
    from models.profile import Profile
    from models.academic_career import AcademicCareer
    
    checklist = {
        "Publication": {
            "year": hasattr(Publication, 'year'),
            "title": hasattr(Publication, 'title'),
            "coauthor": hasattr(Publication, 'coauthor'),
            "abstract": not hasattr(Publication, 'abstract'),
            "description": not hasattr(Publication, 'description'),
            "date": not hasattr(Publication, 'date'),
        },
        "Project": {
            "year": hasattr(Project, 'year'),
            "title": hasattr(Project, 'title'),
            "coauthor": hasattr(Project, 'coauthor'),
            "description": hasattr(Project, 'description'),
            "budget": hasattr(Project, 'budget'),
            "status": hasattr(Project, 'status'),
        },
        "Profile": {
            "grade": hasattr(Profile, 'grade'),
            "specialite": hasattr(Profile, 'specialite'),
            "relations": all(hasattr(Profile, attr) for attr in 
                          ['publications', 'projects', 'distinctions', 
                           'academic_careers', 'cours'])
        },
        "AcademicCareer": {
            "title_formation": hasattr(AcademicCareer, 'title_formation'),
            "diplome": hasattr(AcademicCareer, 'diplome'),
        }
    }
    
    all_passed = True
    for model, checks in checklist.items():
        print(f"\n{model}:")
        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"  {status} {check}")
            if not result:
                all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 TOUS LES MODÈLES SONT CONFORMES !")
    else:
        print("⚠️  Certains modèles ne sont pas conformes")
    print("="*60)
    
    # REMPLACER "return all_passed" par une assertion
    assert all_passed, "Certains modèles ne sont pas conformes au cahier des charges"

def run_all_tests():
    """Exécute tous les tests - Fonction utilitaire pour exécution manuelle"""
    tests = [
        ("User Model", test_user_model),
        ("Profile Model", test_profile_model),
        ("Publication Model", test_publication_model_conforme),
        ("Project Model", test_project_model_conforme),
        ("AcademicCareer Model", test_academic_career_model),
        ("Relations Profile", test_relations_profile),
        ("Champs JSON", test_conformite_champs_json),
        ("Conformité Complète", test_conformite_complete),
    ]
    
    print("Pour exécuter les tests avec pytest: pytest tests/test_models.py -v")
    print("\nPour exécution manuelle (sans pytest), utilisez: python -m pytest tests/test_models.py")

if __name__ == "__main__":
    run_all_tests()