import requests
from settings import ARBISCAN_API_KEY
from logger_config import logger  # Добавляем импорт logger для отладки

def get_token_transactions(wallet_addresses):
    api_key = ARBISCAN_API_KEY
    base_url = "https://api.arbiscan.io/api"
    all_transactions = {}

    for address in wallet_addresses:
        params = {
            "module": "account",
            "action": "tokentx",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "sort": "desc",
            "apikey": api_key
        }
        response = requests.get(base_url, params=params)
        data = response.json()

        if data['status'] == "1" and data['result']:
            transactions = []
            for tx in data['result']:
                # Определяем, является ли кошелёк отправителем или получателем
                is_sender = tx['from'].lower() == address.lower()
                is_receiver = tx['to'].lower() == address.lower()

                transaction = {
                    "tx_hash": tx['hash'],
                    "wallet_address": address,
                    "token_in": "Неизвестно",  # Токен, который мы получили
                    "token_in_address": "",    # Адрес токена, который мы получили
                    "amount_in": "Неизвестно", # Количество токена, который мы получили
                    "token_out": "Неизвестно", # Токен, который мы отдали
                    "token_out_address": "",   # Адрес токена, который мы отдали
                    "amount_out": "Неизвестно",# Количество токена, который мы отдали
                    "usd_value": tx.get('valueUSD', '0')  # Стоимость в USD, если доступна
                }

                # Нормализация адресов контрактов
                contract_address = tx.get('contractAddress', '').lower()
                if contract_address and not contract_address.startswith("0x"):
                    contract_address = "0x" + contract_address

                # Логируем данные транзакции для отладки
                logger.debug(f"Обработка транзакции {tx['hash']}: from={tx['from']}, to={tx['to']}, contractAddress={contract_address}, tokenSymbol={tx.get('tokenSymbol', 'Неизвестно')}")

                # Проверяем все токены в транзакции, чтобы определить IN и OUT
                if is_sender:
                    transaction["token_out"] = tx.get('tokenSymbol', 'Неизвестно')
                    transaction["token_out_address"] = contract_address
                    transaction["amount_out"] = tx.get('value', 'Неизвестно')
                    logger.debug(f"Токен OUT определён: {transaction['token_out']} — {transaction['amount_out']}")
                elif is_receiver:
                    transaction["token_in"] = tx.get('tokenSymbol', 'Неизвестно')
                    transaction["token_in_address"] = contract_address
                    transaction["amount_in"] = tx.get('value', 'Неизвестно')
                    logger.debug(f"Токен IN определён: {transaction['token_in']} — {transaction['amount_in']}")
                else:
                    logger.warning(f"Не удалось определить направление транзакции {tx['hash']} для адреса {address}")

                # Если оба токена (IN и OUT) всё ещё "Неизвестно", пытаемся определить их, анализируя все записи в result
                if transaction["token_in"] == "Неизвестно" or transaction["token_out"] == "Неизвестно":
                    for other_tx in data['result']:
                        other_contract = other_tx.get('contractAddress', '').lower()
                        if not other_contract.startswith("0x"):
                            other_contract = "0x" + other_contract
                        if other_tx['hash'] == tx['hash'] and other_contract != contract_address:
                            if other_tx['from'].lower() == address.lower():
                                transaction["token_out"] = other_tx.get('tokenSymbol', 'Неизвестно')
                                transaction["token_out_address"] = other_contract
                                transaction["amount_out"] = other_tx.get('value', 'Неизвестно')
                                logger.debug(f"Дополнительно определён Токен OUT: {transaction['token_out']} — {transaction['amount_out']}")
                            elif other_tx['to'].lower() == address.lower():
                                transaction["token_in"] = other_tx.get('tokenSymbol', 'Неизвестно')
                                transaction["token_in_address"] = other_contract
                                transaction["amount_in"] = other_tx.get('value', 'Неизвестно')
                                logger.debug(f"Дополнительно определён Токен IN: {transaction['token_in']} — {transaction['amount_in']}")

                # Преобразование значений в читаемый формат (например, из wei в токены, для ERC-20 делим на 10^18)
                try:
                    if transaction["amount_in"] != "Неизвестно":
                        transaction["amount_in"] = str(float(transaction["amount_in"]) / 10**18)  # Пример для ERC-20
                    if transaction["amount_out"] != "Неизвестно":
                        transaction["amount_out"] = str(float(transaction["amount_out"]) / 10**18)  # Пример для ERC-20
                except (ValueError, ZeroDivisionError):
                    pass  # Оставляем "Неизвестно", если преобразование невозможно

                # Устанавливаем URL для токенов
                if transaction["token_in_address"]:
                    transaction["token_in_url"] = f"https://arbiscan.io/token/{transaction['token_in_address']}"
                else:
                    transaction["token_in_url"] = ""

                if transaction["token_out_address"]:
                    transaction["token_out_url"] = f"https://arbiscan.io/token/{transaction['token_out_address']}"
                else:
                    transaction["token_out_url"] = ""

                transactions.append(transaction)
            all_transactions[address] = transactions
        else:
            all_transactions[address] = []

    return all_transactions