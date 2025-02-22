import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from interface import register_handlers, get_main_menu
from arbiscan import get_token_transactions
from message_formatter import format_swap_message
from database import Database
from settings import BOT_TOKEN, CHAT_ID
from logger_config import logger

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db = Database()

# Загружаем настройки из базы
settings = db.get_all_settings()
CHECK_INTERVAL = int(settings["CHECK_INTERVAL"])
LOG_TRANSACTIONS = int(settings["LOG_TRANSACTIONS"])
LOG_SUCCESSFUL_TRANSACTIONS = int(settings["LOG_SUCCESSFUL_TRANSACTIONS"])

logger.info("Статус логов при запуске бота:")
logger.info(f"- Логи транзакций: {'Включены' if LOG_TRANSACTIONS else 'Выключены'}")
logger.info(f"- Логи успешных транзакций: {'Включены' if LOG_SUCCESSFUL_TRANSACTIONS else 'Выключены'}")

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
        try:
            watched_wallets = db.get_all_wallets()
            tracked_tokens = {t["contract_address"].lower(): t for t in db.get_all_tracked_tokens()}
            default_thread_id = 60

            for wallet in watched_wallets:
                wallet_address = wallet["address"]
                wallet_name = wallet["name"]
                transactions = get_token_transactions(wallet_address)

                if not isinstance(transactions, dict) or not transactions:
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
                    await bot.send_message(
                        chat_id=CHAT_ID,
                        message_thread_id=thread_id,
                        text=text,
                        parse_mode=parse_mode,
                        disable_web_page_preview=True
                    )
        except Exception as e:
            logger.error(f"Произошла ошибка: {str(e)}")

        await asyncio.sleep(CHECK_INTERVAL)

async def main():
    logger.info("🚀 Бот запущен и ждет новые транзакции!")
    asyncio.create_task(check_token_transactions())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())