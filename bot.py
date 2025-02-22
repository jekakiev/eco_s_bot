import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from interface import register_handlers, get_main_menu
from arbiscan import get_token_transactions
from message_formatter import format_swap_message
from database import Database
from settings import BOT_TOKEN, CHAT_ID
from logger_config import logger
import time

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db = Database()

# Загружаем настройки из базы с дефолтными значениями, только если их нет
settings = db.get_all_settings()
CHECK_INTERVAL = int(settings.get("CHECK_INTERVAL", "10"))
LOG_TRANSACTIONS = int(settings.get("LOG_TRANSACTIONS", "0"))
LOG_SUCCESSFUL_TRANSACTIONS = int(settings.get("LOG_SUCCESSFUL_TRANSACTIONS", "0"))

logger.info("Статус логов при запуске бота:")
logger.info(f"- Логи транзакций: {'Включены' if LOG_TRANSACTIONS else 'Выключены'}")
logger.info(f"- Логи успешных транзакций: {'Включены' if LOG_SUCCESSFUL_TRANSACTIONS else 'Выключены'}")

# Логируем текущие значения из базы для отладки
logger.debug(f"Загруженные настройки из базы: CHECK_INTERVAL={CHECK_INTERVAL}, LOG_TRANSACTIONS={LOG_TRANSACTIONS}, LOG_SUCCESSFUL_TRANSACTIONS={LOG_SUCCESSFUL_TRANSACTIONS}")

register_handlers(dp)

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("✅ Бот запущен и мониторит транзакции!", reply_markup=get_main_menu())

@dp.message(Command("get_thread_id"))
async def get_thread_id_command(message: types.Message):
    thread_id = message.message_thread_id if message.is_topic_message else "Нет треда (основной чат)"
    await message.answer(f"ID текущего треда: `{thread_id}`", parse_mode="Markdown")

async def check_token_transactions():
    while True:
        start_time = time.time()
        try:
            watched_wallets = db.get_all_wallets()
            tracked_tokens = {t["contract_address"].lower(): t for t in db.get_all_tracked_tokens()}
            default_thread_id = 60

            for wallet in watched_wallets:
                wallet_address = wallet["address"]
                wallet_name = wallet["name"]
                transactions = get_token_transactions(wallet_address)

                if not isinstance(transactions, dict) or not transactions:
                    if LOG_TRANSACTIONS:
                        logger.info(f"get_token_transactions вернула не словарь для кошелька {wallet_address}")
                    continue

                for tx_hash, tx_list in transactions.items():
                    latest_tx = tx_list[0]
                    token_out = latest_tx.get("token_out", "Неизвестно")
                    contract_address = latest_tx.get("token_out_address", "").lower()

                    if db.is_transaction_exist(tx_hash):
                        continue

                    db.add_transaction(tx_hash, wallet_address, token_out, latest_tx.get("usd_value", "0"))

                    thread_id = default_thread_id
                    if contract_address in tracked_tokens:
                        thread_id = tracked_tokens[contract_address]["thread_id"]

                    text, parse_mode = format_swap_message(
                        tx_hash=tx_hash,
                        sender=wallet_name,
                        sender_url=f"https://arbiscan.io/address/{wallet_address}",
                        amount_in=latest_tx.get("amount_in", "Неизвестно"),
                        token_in=latest_tx.get("token_in", "Неизвестно"),
                        token_in_url=f"https://arbiscan.io/token/{latest_tx.get('token_in_address', '')}",
                        amount_out=latest_tx.get("amount_out", "Неизвестно"),
                        token_out=token_out,
                        token_out_url=f"https://arbiscan.io/token/{latest_tx.get('token_out_address', '')}",
                        usd_value=latest_tx.get("usd_value", "Неизвестно")
                    )
                    if LOG_SUCCESSFUL_TRANSACTIONS:
                        logger.info(f"Начинаем проверку новых транзакций для кошелька {wallet_address}")
                        logger.info(f"Найдено соответствие для токена {token_out} в транзакции {tx_hash}")
                        logger.info(f"Сообщение отправлено в тред {thread_id}")
                    await bot.send_message(
                        chat_id=CHAT_ID,
                        message_thread_id=thread_id,
                        text=text,
                        parse_mode=parse_mode,
                        disable_web_page_preview=True
                    )
            logger.info(f"Проверка транзакций заняла {time.time() - start_time} сек")
        except Exception as e:
            logger.error(f"Произошла ошибка: {str(e)}")

        await asyncio.sleep(CHECK_INTERVAL)

async def main():
    logger.info("🚀 Бот запущен и ждет новые транзакции!")
    asyncio.create_task(check_token_transactions())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())