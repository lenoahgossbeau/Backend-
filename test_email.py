import resend
import os
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")

print("🔑 Clé API chargée :", resend.api_key[:10] + "..." if resend.api_key else "❌ Non trouvée")

try:
    email = resend.Emails.send({
        "from": "onboarding@resend.dev",
        "to": ["arnaudchabifor@exemple.com"],  # ← REMPLACE PAR TON EMAIL
        "subject": "Test InchTechs",
        "html": "<h1>✅ Test réussi !</h1><p>L'envoi d'email fonctionne correctement.</p>"
    })
    print("✅ Email envoyé avec succès !")
    print("📧 Détail :", email)
except Exception as e:
    print(f"❌ Erreur: {e}")