import asyncio
import aiohttp
from aiogram import Bot
from database import Database  # Імпортуємо сам клас, а не екземпляр
from utils.logger_config import logger
from config.settings import ARBISCAN_API_KEY, CHAT_ID
import json
import requests  # Для отримання цін через CoinGecko

# Використовуємо глобальний db з bot.py
from bot import db  # Імпортуємо глобальний екземпляр db

async def check_token_transactions(bot: Bot, chat_id: str):
    while True:
        try:
            wallets = db.wallets.get_all_wallets()
            for wallet in wallets:
                wallet_address = wallet[1]  # address
                tokens = db.wallets.get_wallet_by_address(wallet_address)[3] or []  # tokens
                if not tokens:
                    continue
                
                transactions = await get_token_transactions(wallet_address, tokens)
                for tx in transactions:
                    if not tx.get('is_processed', False):
                        tx_hash = tx.get('hash', 'Неизвестно')
                        amount_usd = await convert_to_usd(tx)  # Конвертація суми в долари
                        if amount_usd > 50:  # Фільтрація за сумою
                            await bot.send_message(chat_id, f"Новая транзакция для {wallet_address[-4:]}:\nХеш: {tx_hash}\nСумма: ${amount_usd:.2f}", parse_mode="HTML")
                        tx['is_processed'] = True
                        db.transactions.update_transaction(tx_hash, {'is_processed': True, 'amount_usd': amount_usd})

                # Очищення старих транзакцій (залишаємо лише 20)
                db.transactions.clean_old_transactions(wallet_address, limit=20)

            check_interval = int(db.settings.get_setting("CHECK_INTERVAL", "10"))
            if int(db.settings.get_setting("TRANSACTION_INFO", "1")):  # Оновлено на TRANSACTION_INFO для логів транзакцій
                logger.info(f"Проверка транзакций выполнена. Следующая через {check_interval} секунд.")
            await asyncio.sleep(check_interval)
        except Exception as e:
            if int(db.settings.get_setting("API_ERRORS", "1")):
                logger.error(f"Ошибка при проверке транзакций: {str(e)}")
            await asyncio.sleep(5)

async def get_token_transactions(wallet_address, tokens):
    api_key = ARBISCAN_API_KEY
    base_url = "https://api.arbiscan.io/api"
    params = {
        "module": "account",
        "action": "tokentx",
        "address": wallet_address,
        "startblock": 0,
        "endblock": 99999999,
        "sort": "desc",
        "apikey": api_key
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(base_url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("status") == "1" and data.get("result"):
                    transactions = []
                    for tx in data["result"]:
                        if tx.get("tokenSymbol") in tokens:
                            tx["is_processed"] = False
                            # Отримання decimals для токена
                            token_info = await get_token_info(tx.get("contractAddress", ""))
                            decimals = int(token_info.get("tokenDecimal", 18))
                            # Нормалізація суми
                            value = tx.get("value", "0")
                            try:
                                value_float = float(value) / (10 ** decimals)
                                tx["amount_usd"] = await convert_to_usd({"value": value, "contractAddress": tx.get("contractAddress", "")})
                            except (ValueError, TypeError):
                                tx["amount_usd"] = 0
                            transactions.append(tx)
                    return transactions[:20]  # Повертаємо лише 20 останніх
                else:
                    return []
            else:
                return []

async def get_token_info(contract_address):
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
    async with aiohttp.ClientSession() as session:
        async with session.get(base_url, params=params) as response:
            data = await response.json()
            if data['status'] == "1" and data['result']:
                return {
                    "tokenSymbol": data['result'][0].get('symbol', 'Неизвестно'),
                    "tokenDecimal": data['result'][0].get('decimals', '18')
                }
    return {"tokenSymbol": "Неизвестно", "tokenDecimal": "18"}

async def convert_to_usd(tx):
    try:
        contract_address = tx.get("contractAddress", "")
        value = tx.get("value", "0")
        token_info = await get_token_info(contract_address)
        decimals = int(token_info.get("tokenDecimal", 18))
        value_float = float(value) / (10 ** decimals) if value and value != "0" else 0
        
        # Отримання ціни через DexScreener
        price_usd, price_status = await get_token_price("arbitrum", contract_address)
        if price_usd == "0" or not price_usd:
            return 0  # Якщо ціна не отримана, повертаємо 0
        usd_value = value_float * float(price_usd)
        return usd_value if usd_value > 0 else 0
    except Exception as e:
        if int(db.settings.get_setting("API_ERRORS", "1")):
            logger.error(f"Ошибка конвертации в USD: {str(e)}")
        return 0

async def get_token_price(chain, contract_address):
    if not contract_address or not contract_address.startswith("0x"):
        return "0", "Цена не определена"
    base_url = f"https://api.dexscreener.com/latest/dex/tokens/{chain}/{contract_address}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                response.raise_for_status()
                data = await response.json()
                if 'pair' in data and 'baseToken' in data['pair'] and 'priceUsd' in data['pair']['baseToken']:
                    price_usd = str(data['pair']['baseToken']['priceUsd'])
                    return price_usd, ""
                if int(db.settings.get_setting("API_ERRORS", "1")):
                    logger.warning(f"Не удалось получить цену через DexScreener API для {contract_address}")
                return "0", "Цена не определена"
    except aiohttp.ClientResponseError as e:
        if int(db.settings.get_setting("API_ERRORS", "1")):
            if e.status == 404:
                logger.warning(f"Токен {contract_address} не найден в DexScreener API для {chain}")
            else:
                logger.warning(f"Ошибка при запросе к DexScreener API для {contract_address}: {str(e)}")
        return "0", "Цена не определена"
    except Exception as e:
        if int(db.settings.get_setting("API_ERRORS", "1")):
            logger.warning(f"Ошибка при запросе к DexScreener API для {contract_address}: {str(e)}")
        return "0", "Цена не определена"

async def start_transaction_monitoring(bot: Bot, chat_id: str):
    logger.info("Запуск мониторинга транзакций")
    await check_token_transactions(bot, chat_id)