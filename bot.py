import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import BOT_TOKEN
from arbiscan import get_token_transactions
from message_formatter import format_swap_message
from wallets_config import WATCHED_WALLETS
from threads_config import TOKEN_THREADS, DEFAULT_THREAD_ID
from logger import setup_logger

# Налаштування логування
logger = setup_logger()

# Ініціалізація бота і диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Перевірка нових транзакцій
async def check_token_transactions():
    last_tx_hash = {}

    while True:
        logger.info("🔍 Починаємо перевірку нових транзакцій...")

        for wallet_address, wallet_name in WATCHED_WALLETS.items():
            transactions = get_token_transactions(wallet_address)

            if isinstance(transactions, list) and transactions:
                latest_tx = transactions[0]
                tx_hash = latest_tx["hash"]

                if last_tx_hash.get(wallet_address) != tx_hash:
                    last_tx_hash[wallet_address] = tx_hash
                    token_name = latest_tx.get("token_out", "Other")
                    thread_id = TOKEN_THREADS.get(token_name, DEFAULT_THREAD_ID)

                    text, parse_mode = format_swap_message(
                        tx_hash=tx_hash,
                        sender=wallet_name,
                        sender_url=f"https://arbiscan.io/address/{wallet_address}",
                        amount_in=latest_tx.get("amount_in", "Невідомо"),
                        token_in=latest_tx.get("token_in", "Невідомо"),
                        token_in_url=f"https://arbiscan.io/token/{latest_tx.get('token_in_address', '')}",
                        amount_out=latest_tx.get("amount_out", "Невідомо"),
                        token_out=latest_tx.get("token_out", "Невідомо"),
                        token_out_url=f"https://arbiscan.io/token/{latest_tx.get('token_out_address', '')}",
                        usd_value=latest_tx.get("usd_value", "Невідомо")
                    )

                    logger.info(f"📤 Відправка повідомлення в тред {thread_id} для токена {token_name}")

                    await bot.send_message(
                        chat_id=-1002458140371, 
                        message_thread_id=thread_id,
                        text=text,
                        parse_mode=parse_mode,
                        disable_web_page_preview=True
                    )

            else:
                logger.warning(f"⚠️ Не знайдено транзакцій для {wallet_address}")

        logger.info("⏳ Чекаємо наступний цикл перевірки...")
        await asyncio.sleep(10)

# Обробник команди /start
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("✅ Бот запущено!")

# Обробник команди /get_chat_id
@dp.message(Command("get_chat_id"))
async def get_chat_id(message: types.Message):
    thread_id = message.message_thread_id
    chat_info = f"🆔 Chat ID: `{message.chat.id}`"

    if thread_id:
        chat_info += f"\n🧵 Thread ID: `{thread_id}`"

    await message.answer(chat_info, parse_mode="Markdown")

# Запуск бота
async def main():
    logger.info("🚀 Бот запущено!")
    asyncio.create_task(check_token_transactions())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
