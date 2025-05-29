import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Antilopay API настройки
ANTILOPAY_API_URL = os.getenv('ANTILOPAY_API_URL', 'https://api.antilopay.com')
ANTILOPAY_SECRET_ID = os.getenv('ANTILOPAY_SECRET_ID')
ANTILOPAY_PRIVATE_KEY = os.getenv('ANTILOPAY_PRIVATE_KEY')
ANTILOPAY_PROJECT_ID = os.getenv('ANTILOPAY_PROJECT_ID')

# Google Sheets настройки
GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')

# Менеджер чат ID
MANAGER_CHAT_ID = os.getenv('MANAGER_CHAT_ID')

# Игровые консоли и позиции
CONSOLES = {
    'PS4': ['П2', 'П3', 'П3.1'],
    'PS5': ['П2', 'П3', 'П3.1']
} 

# Названия способов оплаты
PAYMENT_METHOD_NAMES = {
    "CARD_RU": "💳 Банковская карта",
    "SBER_PAY": "🟢 SberPay", 
    "SBP": "⚡ СБП"
}