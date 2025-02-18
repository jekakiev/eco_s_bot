import requests
import config  # Імпортуємо API-ключ

ARBISCAN_API_URL = "https://api.arbiscan.io/api"
TOKEN_ADDRESS = "0xcdfb52783591231ea098d9e3207dc6c699513b00"  # Адреса токена, який відстежуємо

def get_token_transactions(wallet_address):
    """Отримує останні транзакції для конкретного токена"""
    params = {
        "module": "account",
        "action": "tokentx",
        "contractaddress": TOKEN_ADDRESS,  # Фільтр по конкретному токену
        "address": wallet_address,
        "startblock": 0,
        "endblock": 99999999,
        "sort": "desc",
        "apikey": config.ARBISCAN_API_KEY
    }

    response = requests.get(ARBISCAN_API_URL, params=params)

    if response.status_code == 200:
        data = response.json()
        if data["status"] == "1":
            return data["result"][:5]  # Беремо лише останні 5 транзакцій
        else:
            return f"❌ Помилка API: {data['message']}"
    else:
        return f"❌ Помилка запиту: {response.status_code}"
