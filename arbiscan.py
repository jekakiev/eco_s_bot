import requests
from settings import ARBISCAN_API_KEY

ARBISCAN_API_URL = "https://api.arbiscan.io/api"

def get_token_transactions(wallet_address):
    """Отримує останні транзакції для гаманця"""
    params = {
        "module": "account",
        "action": "tokentx",
        "address": wallet_address,
        "startblock": 0,
        "endblock": 99999999,
        "sort": "desc",
        "apikey": ARBISCAN_API_KEY
    }

    response = requests.get(ARBISCAN_API_URL, params=params)

    if response.status_code == 200:
        data = response.json()

        if data.get("status") == "1" and "result" in data:
            transactions = data["result"]
            tx_dict = {}

            for tx in transactions:
                tx_hash = tx["hash"]

                if tx_hash not in tx_dict:
                    tx_dict[tx_hash] = []

                tx_dict[tx_hash].append(tx)

            # Логування без виводу всіх транзакцій
            print(f"✅ Отримано {len(transactions)} транзакцій. Останній хеш: {transactions[0]['hash']}")
            return tx_dict  
        else:
            print(f"❌ Помилка API: {data.get('message', 'Немає даних')}")
            return {}
    else:
        print(f"❌ Помилка запиту: {response.status_code}")
        return {}
