import asyncio
import aiohttp
from aiogram import Bot
from database import Database
from utils.logger_config import logger
from config.settings import ARBISCAN_API_KEY, CHAT_ID
import json

db = Database()

async def check_token_transactions(bot: Bot, chat_id: str):
    while True:
        try:
            wallets = db.wallets.get_all_wallets()
            for wallet in wallets:
                wallet_address = wallet[1]  # address (індекс 1 у кортежі)
                tokens = db.wallets.get_wallet_by_address(wallet_address)[3] or []  # tokens (індекс 3 у кортежі)
                if not tokens:
                    continue
                
                transactions = await get_token_transactions(wallet_address, tokens)
                for tx in transactions:
                    if not tx.get('is_processed', False):
                        tx_hash = tx.get('hash', 'Неизвестно')
                        amount_usd = tx.get('amount_usd', 0)
                        if amount_usd > 50:  # Фільтрація за сумою
                            await bot.send_message(chat_id, f"Новая транзакция для {wallet_address[-4:]}:\nХеш: {tx_hash}\nСумма: ${amount_usd:.2f}", parse_mode="HTML")
                        tx['is_processed'] = True
                        db.transactions.update_transaction(tx_hash, {'is_processed': True})  # Припускаємо, що є метод update_transaction

            check_interval = int(db.settings.get_setting("CHECK_INTERVAL", "10"))  # Оновлено на db.settings.get_setting
            if int(db.settings.get_setting("API_ERRORS", "1")):  # Оновлено на db.settings.get_setting
                logger.info(f"Проверка транзакций выполнена. Следующая через {check_interval} секунд.")
            await asyncio.sleep(check_interval)
        except Exception as e:
            if int(db.settings.get_setting("API_ERRORS", "1")):  # Оновлено на db.settings.get_setting
                logger.error(f"Ошибка при проверке транзакций: {str(e)}")
            await asyncio.sleep(5)  # Пауза перед повторною спробою

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
                            # Припускаємо, що потрібно додати amount_usd (тут спрощено, потрібно інтеграцію з API цін)
                            tx["amount_usd"] = 0  # Заміни на реальну логіку конвертації
                            tx["is_processed"] = False
                            transactions.append(tx)
                    return transactions[:20]  # Повертаємо лише 20 останніх
                else:
                    return []
            else:
                return []

async def start_transaction_monitoring(bot: Bot, chat_id: str):
    logger.info("Запуск мониторинга транзакций")
    await check_token_transactions(bot, chat_id)