import sys
from pathlib import Path
from datetime import datetime
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class ConformityTester:
    def __init__(self):
        self.results = []
        self.start = datetime.now()

    def log(self, name, ok, msg=""):
        status = "✅ PASSÉ" if ok else "❌ ÉCHOUÉ"
        if msg:
            status += f" ({msg})"
        self.results.append(ok)
        print(status, name)
        return ok

    def test_app(self):
        r = client.get("/")
        return self.log("Application démarre", r.status_code in [200, 302])

    def test_db(self):
        r = client.get("/health")
        return self.log("DB connectée", r.status_code == 200)

    def test_models(self):
        from models.publication import Publication
        from models.project import Project

        for field in ["year", "title", "coauthor"]:
            if not hasattr(Publication, field):
                return self.log("Publication modèle", False)

        for field in ["year", "title", "coauthor"]:
            if not hasattr(Project, field):
                return self.log("Project modèle", False)

        return self.log("Modèles conformes", True)

    def test_api(self):
        r = client.get("/api/info")
        return self.log("API info", r.status_code == 200)

    def report(self):
        total = len(self.results)
        ok = sum(self.results)
        score = int(ok / total * 100)
        print("\n📊 SCORE:", score, "%")

        if score >= 80:
            print("🎉 BACKEND CONFORME")
            return True
        print("⚠️ NON CONFORME")
        return False

    def run(self):
        print("🔍 TEST DE CONFORMITÉ\n")
        self.test_app()
        self.test_db()
        self.test_models()
        self.test_api()
        return self.report()


if __name__ == "__main__":
    tester = ConformityTester()
    sys.exit(0 if tester.run() else 1)
