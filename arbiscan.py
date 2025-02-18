import requests
import config  

ARBISCAN_API_URL = "https://api.arbiscan.io/api"
TOKEN_ADDRESS = "0xcdfb52783591231ea098d9e3207dc6c699513b00"

def get_token_transactions(wallet_address):
    """Получает последние транзакции для конкретного токена"""
    params = {
        "module": "account",
        "action": "tokentx",
        "address": wallet_address,  # Убираем contractaddress, чтобы получить все токены
        "startblock": 0,
        "endblock": 99999999,
        "sort": "desc",
        "apikey": config.ARBISCAN_API_KEY
    }

    response = requests.get(ARBISCAN_API_URL, params=params)

    if response.status_code == 200:
        data = response.json()
        print("🔍 API Response:", data)  

        if data.get("status") == "1" and "result" in data:
            transactions = data["result"]
            tx_dict = {}  

            for tx in transactions:
                tx_hash = tx["hash"]

                if tx_hash not in tx_dict:
                    tx_dict[tx_hash] = []

                tx_dict[tx_hash].append(tx)

            return tx_dict  
        else:
            print(f"❌ Ошибка API: {data.get('message', 'Нет данных')}")
            return {}
    else:
        print(f"❌ Ошибка запроса: {response.status_code}")
        return {}
