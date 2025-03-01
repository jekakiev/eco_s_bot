# /utils/arbiscan.py
import asyncio
import aiohttp
from config.settings import ARBISCAN_API_KEY
from utils.logger_config import logger, should_log
from app_config import db

async def get_token_info(contract_address):
    if not contract_address or not contract_address.startswith("0x"):
        if should_log("api_errors"):
            logger.warning(f"Некорректный адрес контракта: {contract_address}")
        return {"tokenSymbol": "Неизвестно", "tokenDecimal": "18"}
    api_key = ARBISCAN_API_KEY
    base_url = "https://api.arbiscan.io/api"
    params = {
        "module": "token",
        "action": "tokeninfo",
        "contractaddress": contract_address,
        "apikey": api_key
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                data = await response.json()
                if should_log("debug"):
                    logger.debug(f"Ответ Arbiscan для get_token_info {contract_address}: {data}")
                if data.get('status') == "1" and data.get('result'):
                    symbol = data['result'][0].get('symbol', 'Неизвестно')
                    decimals = data['result'][0].get('decimals', '18')
                    if should_log("debug"):
                        logger.debug(f"Получено имя токена: {symbol}, decimals: {decimals}")
                    return {
                        "tokenSymbol": symbol if symbol else "Неизвестно",
                        "tokenDecimal": decimals if decimals else "18"
                    }
                if should_log("api_errors"):
                    logger.warning(f"Не удалось получить информацию о токене {contract_address}: {data.get('message', 'Нет данных')}")
                return {"tokenSymbol": "Неизвестно", "tokenDecimal": "18"}
    except aiohttp.ClientError as e:
        logger.error(f"Ошибка сети при запросе к Arbiscan для {contract_address}: {str(e)}")
        return {"tokenSymbol": "Неизвестно", "tokenDecimal": "18"}
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении данных токена {contract_address}: {str(e)}")
        return {"tokenSymbol": "Неизвестно", "tokenDecimal": "18"}

async def get_token_transactions(wallet_addresses):
    api_key = ARBISCAN_API_KEY
    base_url = "https://api.arbiscan.io/api"
    all_transactions = {}
    
    async with aiohttp.ClientSession() as session:
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
            async with session.get(base_url, params=params) as response:
                data = await response.json()
                if should_log("debug"):
                    logger.debug(f"Полный JSON-ответ Arbiscan для адреса {address}: {data}")
                
                if data['status'] == "1" and data['result']:
                    transactions = []
                    for tx in data['result']:
                        is_sender = tx['from'].lower() == address.lower()
                        is_receiver = tx['to'].lower() == address.lower()

                        transaction = {
                            "tx_hash": tx['hash'],
                            "wallet_address": address,
                            "token_in": "Неизвестно",
                            "token_in_address": "",
                            "amount_in": "Неизвестно",
                            "token_out": "Неизвестно",
                            "token_out_address": "",
                            "amount_out": "Неизвестно",
                            "usd_value": "0"
                        }

                        contract_address = tx.get('contractAddress', '').lower()
                        if contract_address and not contract_address.startswith("0x"):
                            contract_address = "0x" + contract_address

                        token_info = await get_token_info(contract_address)
                        token_symbol = tx.get('tokenSymbol', token_info['tokenSymbol'])
                        try:
                            token_decimal = int(token_info['tokenDecimal'])
                        except ValueError:
                            token_decimal = 18
                            if should_log("api_errors"):
                                logger.warning(f"Некорректное значение decimals для {contract_address}: {token_info['tokenDecimal']}")

                        if should_log("debug"):
                            logger.debug(f"Обработка транзакции {tx['hash']}: from={tx['from']}, to={tx['to']}, contractAddress={contract_address}")

                        value = tx.get('value', '0')
                        try:
                            value_float = float(value) / (10 ** token_decimal)
                        except (ValueError, TypeError):
                            value_float = "Неизвестно"
                            if should_log("api_errors"):
                                logger.warning(f"Ошибка преобразования значения для транзакции {tx['hash']}: {value}")

                        if is_sender:
                            transaction["token_out"] = token_symbol
                            transaction["token_out_address"] = contract_address
                            transaction["amount_out"] = str(value_float) if value_float != "Неизвестно" else "Неизвестно"
                        elif is_receiver:
                            transaction["token_in"] = token_symbol
                            transaction["token_in_address"] = contract_address
                            transaction["amount_in"] = str(value_float) if value_float != "Неизвестно" else "Неизвестно"

                        if transaction["token_in"] == "Неизвестно" or transaction["token_out"] == "Неизвестно":
                            for other_tx in data['result']:
                                other_contract = other_tx.get('contractAddress', '').lower()
                                if not other_contract.startswith("0x"):
                                    other_contract = "0x" + other_contract
                                if other_tx['hash'] == tx['hash'] and other_contract != contract_address:
                                    other_token_info = await get_token_info(other_contract)
                                    other_token_symbol = other_tx.get('tokenSymbol', other_token_info['tokenSymbol'])
                                    try:
                                        other_token_decimal = int(other_token_info['tokenDecimal'])
                                    except ValueError:
                                        other_token_decimal = 18
                                        if should_log("api_errors"):
                                            logger.warning(f"Некорректное значение decimals для {other_contract}: {other_token_info['tokenDecimal']}")
                                    other_value = other_tx.get('value', '0')
                                    try:
                                        other_value_float = float(other_value) / (10 ** other_token_decimal)
                                    except (ValueError, TypeError):
                                        other_value_float = "Неизвестно"
                                        if should_log("api_errors"):
                                            logger.warning(f"Ошибка преобразования значения для связанной транзакции {other_tx['hash']}: {other_value}")

                                    if other_tx['from'].lower() == address.lower():
                                        transaction["token_out"] = other_token_symbol
                                        transaction["token_out_address"] = other_contract
                                        transaction["amount_out"] = str(other_value_float) if other_value_float != "Неизвестно" else "Неизвестно"
                                    elif other_tx['to'].lower() == address.lower():
                                        transaction["token_in"] = other_token_symbol
                                        transaction["token_in_address"] = other_contract
                                        transaction["amount_in"] = str(other_value_float) if other_value_float != "Неизвестно" else "Неизвестно"

                        if transaction["token_in_address"]:
                            transaction["token_in_url"] = f"https://arbiscan.io/token/{transaction['token_in_address']}"
                        else:
                            transaction["token_in_url"] = ""

                        if transaction["token_out_address"]:
                            transaction["token_out_url"] = f"https://arbiscan.io/token/{transaction['token_out_address']}"
                        else:
                            transaction["token_out_url"] = ""

                        transaction["usd_value"] = tx.get('valueUSD', '0')
                        if transaction["usd_value"] == "0":
                            if should_log("api_errors"):
                                logger.warning(f"Не удалось получить valueUSD для транзакции {tx['hash']}")

                        transactions.append(transaction)
                        await asyncio.sleep(0.05)

                    all_transactions[address] = transactions
                else:
                    if should_log("api_errors"):
                        logger.error(f"Ошибка в ответе Arbiscan для адреса {address}: {data.get('message', 'Нет данных')}")
                    all_transactions[address] = []
    
    return all_transactions