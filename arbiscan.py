import requests
from settings import ARBISCAN_API_KEY
import logging

logger = logging.getLogger('main_logger')

def get_token_transactions(wallet_addresses):
    """
    Получает последние 10 транзакций для списка кошельков, разбивая запросы на части по 5 адресов
    без дополнительных задержек, но с учётом лимита Arbiscan (5 запросов/сек).
    """
    if not wallet_addresses or not isinstance(wallet_addresses, (list, str)):
        return {}

    # Если передан один адрес как строка, конвертируем в список
    if isinstance(wallet_addresses, str):
        wallet_addresses = [wallet_addresses]

    # Ограничиваем количество адресов в одном запросе (5 — безопасный лимит для tokentx)
    max_addresses_per_request = 5
    all_transactions = {}

    for i in range(0, len(wallet_addresses), max_addresses_per_request):
        chunk_addresses = wallet_addresses[i:i + max_addresses_per_request]
        addresses = ",".join(chunk_addresses)
        
        # Параметры запросa для tokentx
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
                logger.error(f"Arbiscan вернул ошибку: {data.get('message', 'Неизвестная ошибка')} для адресов {chunk_addresses}")
                continue  # Пропускаем этот чанк, если ошибка

            # Логируем полный ответ Arbiscan для анализа
            logger.debug(f"Полный ответ Arbiscan для адресов {chunk_addresses}: {data}")

            # Группируем транзакции по hash, чтобы обработать свопы/переводы
            tx_by_hash = {}
            for tx in data.get("result", []):
                tx_hash = tx.get("hash")
                if tx_hash not in tx_by_hash:
                    tx_by_hash[tx_hash] = []
                tx_by_hash[tx_hash].append(tx)

            # Парсим транзакции, группируя их по кошелькам
            for wallet_address in chunk_addresses:
                wallet_address_lower = wallet_address.lower()
                for tx_list in tx_by_hash.values():
                    token_in = "Неизвестно"
                    token_out = "Неизвестно"
                    amount_in = "0"
                    amount_out = "0"
                    token_in_address = ""
                    token_out_address = ""
                    usd_value = "Неизвестно"  # Пока оставим, добавим API курсов позже

                    for tx in tx_list:
                        # Получаем децималы токена для конвертации из wei
                        decimals = int(tx.get("tokenDecimal", "18"))  # По умолчанию 18, как для ERC-20
                        value = int(tx.get("value", "0"))  # Убедимся, что value — целое число
                        readable_value = value / (10 ** decimals) if decimals > 0 else value

                        if tx["to"].lower() == wallet_address_lower:
                            # Входящая транзакция
                            token_in = tx.get("tokenSymbol", "Неизвестно")
                            token_in_address = tx.get("contractAddress", "")
                            amount_in = str(readable_value)
                        elif tx["from"].lower() == wallet_address_lower:
                            # Исходящая транзакция
                            token_out = tx.get("tokenSymbol", "Неизвестно")
                            token_out_address = tx.get("contractAddress", "")
                            amount_out = str(readable_value)

                    if token_in != "Неизвестно" or token_out != "Неизвестно":
                        if wallet_address_lower not in all_transactions:
                            all_transactions[wallet_address_lower] = []
                        all_transactions[wallet_address_lower].append({
                            "tx_hash": tx_list[0].get("hash"),
                            "token_in": token_in,
                            "token_in_address": token_in_address,
                            "amount_in": amount_in,
                            "token_out": token_out,
                            "token_out_address": token_out_address,
                            "amount_out": amount_out,
                            "usd_value": usd_value
                        })

            logger.info(f"Успешно получены транзакции для {len(chunk_addresses)} адресов: {chunk_addresses}")

        except requests.RequestException as e:
            logger.error(f"Ошибка при запросе к Arbiscan для адресов {chunk_addresses}: {str(e)}")
            continue

        except Exception as e:
            logger.error(f"Произошла ошибка обработки ответа Arbiscan для адресов {chunk_addresses}: {str(e)}")
            continue

    return all_transactions