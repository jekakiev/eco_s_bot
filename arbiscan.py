import requests
from settings import ARBISCAN_API_KEY

ARBISCAN_API_URL = "https://api.arbiscan.io/api"

def get_token_transactions(wallet_address):
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
            return tx_dict
        return {}
    return {}