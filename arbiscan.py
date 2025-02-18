import requests
import config  # Импортируем API-ключ

ARBISCAN_API_URL = "https://api.arbiscan.io/api"
TOKEN_ADDRESS = "0xcdfb52783591231ea098d9e3207dc6c699513b00"  # Адрес токена, который отслеживаем

def get_token_transactions(wallet_address):
    """Получает последние транзакции для конкретного токена"""
    params = {
        "module": "account",
        "action": "tokentx",
        "contractaddress": TOKEN_ADDRESS,  # Фильтр по конкретному токену
        "address": wallet_address,
        "startblock": 0,
        "endblock": 99999999,
        "sort": "desc",
        "apikey": config.ARBISCAN_API_KEY
    }

    response = requests.get(ARBISCAN_API_URL, params=params)

    # Проверяем статус ответа
    if response.status_code == 200:
        data = response.json()
        
        # 🔍 Логируем ответ API в консоль для дебага
        print("🔍 API Response:", data)
        
        if data.get("status") == "1" and "result" in data:
            return data["result"][:5]  # Берём только последние 5 транзакций
        else:
            print(f"❌ Ошибка API: {data.get('message', 'Нет данных')}")
            return []
    else:
        print(f"❌ Ошибка запроса: {response.status_code}")
        return []
