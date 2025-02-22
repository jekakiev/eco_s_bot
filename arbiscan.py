import requests
from settings import ARBISCAN_API_KEY
import logging

logger = logging.getLogger('main_logger')

def get_token_transactions(wallet_addresses):
    """
    Получает последние 10 транзакций для списка кошельков одним запросом.
    Использует эндпоинт tokentx с параметрами для нескольких адресов и ограничением на 10 записей.
    """
    if not wallet_addresses or not isinstance(wallet_addresses, (list, str)):
        return {}

    # Если передан один адрес как строка, конвертируем в список
    if isinstance(wallet_addresses, str):
        wallet_addresses = [wallet_addresses]

    # Объединяем адреса в строку через запятую
    addresses = ",".join(wallet_addresses)
    
    # Параметры запроса
    params = {
        "module": "account",
        "action": "tokentx",
        "address": addresses,
        "startblock": 0,  # Начальный блок (0 для всех блоков, но ограничим позже)
        "endblock": 99999999,  # Конечный блок (максимум)
        "sort": "desc",  # Сортировка по убыванию (новые транзакции первыми)
        "offset": 0,  # Начало пагинации
        "limit": 10,  # Ограничение на 10 последних транзакций
        "apikey": ARBISCAN_API_KEY
    }

    try:
        response = requests.get("https://api.arbiscan.io/api", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "1":
            logger.error(f"Arbiscan вернул ошибку: {data.get('message', 'Неизвестная ошибка')}")
            return {}

        # Парсим транзакции, группируя их по кошелькам
        transactions = {}
        for tx in data.get("result", []):
            wallet_address = tx.get("to", tx.get("from", "Unknown")).lower()  # Адрес отправителя или получателя
            if wallet_address not in transactions:
                transactions[wallet_address] = []
            transactions[wallet_address].append({
                "tx_hash": tx.get("hash"),
                "token_in": tx.get("tokenSymbol", "Unknown"),
                "token_in_address": tx.get("contractAddress", ""),
                "amount_in": tx.get("value", "0"),
                "token_out": tx.get("tokenSymbol", "Unknown"),
                "token_out_address": tx.get("contractAddress", ""),
                "amount_out": tx.get("value", "0"),
                "usd_value": tx.get("valueUSD", "0")  # Предполагаем, что есть поле USD, если нет — уточним
            })
        return transactions

    except requests.RequestException as e:
        logger.error(f"Ошибка при запросе к Arbiscan: {str(e)}")
        return {}

    except Exception as e:
        logger.error(f"Произошла ошибка обработки ответа Arbiscan: {str(e)}")
        return {}