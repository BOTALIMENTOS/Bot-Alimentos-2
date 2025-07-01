import requests
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("7591153745:AAG2lGLvHCHUxfv9LQSSJb2Sv1CRxUDFCyM")
WEBHOOK_URL = "https://bot-alimentos-2.onrender.com/webhook"

response = requests.get(
    f"https://api.telegram.org/bot{7591153745:AAG2lGLvHCHUxfv9LQSSJb2Sv1CRxUDFCyM}/setWebhook?url={WEBHOOK_URL}"
)

print("📡 Webhook registrado:", response.json())
