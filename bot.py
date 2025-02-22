import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from interface import register_handlers, get_main_menu
from arbiscan import get_token_transactions
from message_formatter import format_swap_message
from database import Database
from settings import BOT_TOKEN, CHECK_INTERVAL, CHAT_ID, LOG_TRANSACTIONS, LOG_SUCCESSFUL_TRANSACTIONS
from logger_config import logger
from threads_config import DEFAULT_THREAD_ID, TOKEN_CONFIG

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db = Database()

logger.info("Статус логов при запуске бота:")
logger.info(f"- Логи транзакций: {'Включены' if LOG_TRANSACTIONS else 'Выключены'} (LOG_TRANSACTIONS = {LOG_TRANSACTIONS})")
logger.info(f"- Логи успешных транзакций: {'Включены' if LOG_SUCCESSFUL_TRANSACTIONS else 'Выключены'} (LOG_SUCCESSFUL_TRANSACTIONS = {LOG_SUCCESSFUL_TRANSACTIONS})")

register_handlers(dp)

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("✅ Бот запущен и мониторит транзакции!", reply_markup=get_main_menu())

async def check_token_transactions():
    while True:
        try:
            watched_wallets = db.get_all_wallets()
            for wallet in watched_wallets:
                wallet_address = wallet["address"]
                wallet_name = wallet["name"]
                transactions = get_token_transactions(wallet_address)

                if not isinstance(transactions, dict):
                    continue

                if not transactions:
                    continue

                for tx_hash, tx_list in transactions.items():
                    latest_tx = tx_list[0]
                    token_out = latest_tx.get("token_out", "Неизвестно")
                    contract_address = latest_tx.get("token_out_address", "").lower()

                    if db.is_transaction_exist(tx_hash):
                        continue

                    db.add_transaction(tx_hash, wallet_address, token_out, latest_tx.get("usd_value", "0"))

                    thread_id = DEFAULT_THREAD_ID
                    for token_name, config in TOKEN_CONFIG.items():
                        if contract_address == config["contract_address"].lower():
                            thread_id = config["thread_id"]
                            break

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