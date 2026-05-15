# email_service.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def send_activation_email_brevo(to_email: str, activation_link: str, first_name: str = "") -> bool:
    """
    Envoie un email d'activation via l'API REST de Brevo.
    Cette méthode ne dépend pas du SDK 'brevo-python' et évite les erreurs de compatibilité.
    """
    api_key = os.getenv("BREVO_API_KEY")
    if not api_key:
        print("❌ Clé API Brevo manquante dans le fichier .env")
        return False

    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }

    # Construction du contenu de l'email
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <body>
        <h1>Bienvenue sur InchTechs !</h1>
        <p>Bonjour {first_name if first_name else 'cher chercheur'},</p>
        <p>Cliquez sur le lien ci-dessous pour activer votre compte :</p>
        <a href="{activation_link}">Activer mon compte</a>
        <p>Lien : {activation_link}</p>
        <p>Ce lien expire dans 24 heures.</p>
        <hr>
        <p><small>InchTechs - Plateforme de portfolios pour chercheurs</small></p>
    </body>
    </html>
    """

    payload = {
        "sender": {"name": "InchTechs", "email": "noreply@inchtechs.com"},
        "to": [{"email": to_email, "name": first_name if first_name else to_email}],
        "subject": "Activez votre compte chercheur InchTechs",
        "htmlContent": html_content
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 201:
            print(f"✅ Email d'activation envoyé avec succès à {to_email} via Brevo (API REST)")
            return True
        else:
            print(f"❌ Erreur Brevo (API REST): {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi de l'email: {e}")
        return False