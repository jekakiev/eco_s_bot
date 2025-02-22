import requests
import time
from settings import ARBISCAN_API_KEY
import logging

logger = logging.getLogger('main_logger')

def get_token_transactions(wallet_addresses):
    """
    Получает последние 10 транзакций для списка кошельков, разбивая запросы на части по 10 адресов
    с учётом лимита Arbiscan (5 запросов/сек).
    """
    if not wallet_addresses or not isinstance(wallet_addresses, (list, str)):
        return {}

    # Если передан один адрес как строка, конвертируем в список
    if isinstance(wallet_addresses, str):
        wallet_addresses = [wallet_addresses]

    # Ограничиваем количество адресов в одном запросе (например, 10 — безопасный лимит для tokentx)
    max_addresses_per_request = 10
    all_transactions = {}

    for i in range(0, len(wallet_addresses), max_addresses_per_request):
        chunk_addresses = wallet_addresses[i:i + max_addresses_per_request]
        addresses = ",".join(chunk_addresses)
        
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
            # Задержка, чтобы не превышать лимит 5 запросов/сек
            time.sleep(0.2)  # ~5 запросов в секунду (0.2 сек между запросами)
            
            response = requests.get("https://api.arbiscan.io/api", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "1":
                logger.error(f"Arbiscan вернул ошибку: {data.get('message', 'Неизвестная ошибка')}")
                continue  # Пропускаем этот чанк, если ошибка

            # Парсим транзакции, группируя их по кошелькам
            for tx in data.get("result", []):
                wallet_address = tx.get("to", tx.get("from", "Unknown")).lower()  # Адрес отправителя или получателя
                if wallet_address not in all_transactions:
                    all_transactions[wallet_address] = []
                all_transactions[wallet_address].append({
                    "tx_hash": tx.get("hash"),
                    "token_in": tx.get("tokenSymbol", "Unknown"),
                    "token_in_address": tx.get("contractAddress", ""),
                    "amount_in": tx.get("value", "0"),
                    "token_out": tx.get("tokenSymbol", "Unknown"),
                    "token_out_address": tx.get("contractAddress", ""),
                    "amount_out": tx.get("value", "0"),
                    "usd_value": tx.get("valueUSD", "0")  # Предполагаем, что есть поле USD, если нет — уточним
                })

            logger.info(f"Успешно получены транзакции для {len(chunk_addresses)} адресов")

        except requests.RequestException as e:
            logger.error(f"Ошибка при запросе к Arbiscan: {str(e)}")
            continue

        except Exception as e:
            logger.error(f"Произошла ошибка обработки ответа Arbiscan: {str(e)}")
            continue

    return all_transactions