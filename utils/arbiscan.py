import requests
import time
from config.settings import ARBISCAN_API_KEY
from utils.logger_config import logger

def get_token_info(contract_address):
    if not contract_address or not contract_address.startswith("0x"):
        return {"tokenSymbol": "Неизвестно", "tokenDecimal": "18"}
    api_key = ARBISCAN_API_KEY
    base_url = "https://api.arbiscan.io/api"
    params = {
        "module": "token",
        "action": "tokeninfo",
        "contractaddress": contract_address,
        "apikey": api_key
    }
    response = requests.get(base_url, params=params)
    data = response.json()
    if data['status'] == "1" and data['result']:
        return {
            "tokenSymbol": data['result'][0].get('symbol', 'Неизвестно'),
            "tokenDecimal": data['result'][0].get('decimals', '18')
        }
    return {"tokenSymbol": "Неизвестно", "tokenDecimal": "18"}

def get_token_price(chain, contract_address):
    if not contract_address or not contract_address.startswith("0x"):
        return "0", "Цена не определена"
    base_url = "https://api.dexscreener.com/latest/dex/tokens/{}/{}".format(chain, contract_address)
    headers = {}
    try:
        response = requests.get(base_url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if 'pair' in data and 'baseToken' in data['pair'] and 'priceUsd' in data['pair']['baseToken']:
            price_usd = str(data['pair']['baseToken']['priceUsd'])
            return price_usd, ""
        logger.warning(f"Не удалось получить цену через DexScreener API для {contract_address}")
        return "0", "Цена не определена"
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logger.warning(f"Токен {contract_address} не найден в DexScreener API для {chain}")
        else:
            logger.warning(f"Ошибка при запросе к DexScreener API для {contract_address}: {str(e)}")
        return "0", "Цена не определена"
    except requests.exceptions.RequestException as e:
        logger.warning(f"Ошибка при запросе к DexScreener API для {contract_address}: {str(e)}")
        return "0", "Цена не определена"

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

                token_info = get_token_info(contract_address)
                token_symbol = tx.get('tokenSymbol', token_info['tokenSymbol'])
                try:
                    token_decimal = int(token_info['tokenDecimal'])
                except ValueError:
                    token_decimal = 18

                logger.debug(f"Обработка транзакции {tx['hash']}: from={tx['from']}, to={tx['to']}, contractAddress={contract_address}")

                value = tx.get('value', '0')
                try:
                    value_float = float(value) / (10 ** token_decimal)
                except (ValueError, TypeError):
                    value_float = "Неизвестно"

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
                            other_token_info = get_token_info(other_contract)
                            other_token_symbol = other_tx.get('tokenSymbol', other_token_info['tokenSymbol'])
                            try:
                                other_token_decimal = int(other_token_info['tokenDecimal'])
                            except ValueError:
                                other_token_decimal = 18
                            other_value = other_tx.get('value', '0')
                            try:
                                other_value_float = float(other_value) / (10 ** other_token_decimal)
                            except (ValueError, TypeError):
                                other_value_float = "Неизвестно"

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
                    logger.warning(f"Не удалось получить valueUSD для транзакции {tx['hash']}")

                if transaction["usd_value"] == "0" and (transaction["token_in_address"] or transaction["token_out_address"]):
                    try:
                        for token_address_key in ["token_in_address", "token_out_address"]:
                            token_address = transaction[token_address_key]
                            if token_address:
                                price_usd, price_status = get_token_price("arbitrum", token_address)
                                if price_usd != "0":
                                    amount_key = "amount_in" if token_address_key == "token_in_address" else "amount_out"
                                    amount = transaction[amount_key]
                                    if amount != "Неизвестно":
                                        amount_float = float(amount)
                                        transaction["usd_value"] = str(amount_float * float(price_usd))
                                        logger.debug(f"Получена стоимость через DexScreener: ${transaction['usd_value']}")
                                    break
                    except Exception as e:
                        logger.warning(f"Не удалось получить стоимость через DexScreener: {str(e)}")

                transactions.append(transaction)
                time.sleep(0.1)

            all_transactions[address] = transactions
        else:
            all_transactions[address] = []

    return all_transactions