import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import BOT_TOKEN
from interface import register_handlers, get_main_menu
from arbiscan import get_token_transactions
from message_formatter import format_swap_message
from database import Database
from threads_config import TOKEN_CONFIG, DEFAULT_THREAD_ID

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Ініціалізуємо бота, диспетчер та базу даних
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db = Database()

# Реєструємо хендлери
register_handlers(dp)

# Налаштування
CHECK_INTERVAL = 2  # Перевірка кожні 2 секунди
CHAT_ID = -1002458140371  # Chat ID групи

# Обробник команди /start (головне меню)
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("✅ Бот запущений та моніторить транзакції!", reply_markup=get_main_menu())

# Обробник команди /get_chat_id (Отримання ID треда)
@dp.message(Command("get_chat_id"))
async def get_chat_id(message: types.Message):
    thread_id = message.message_thread_id  # ID треда (гілки)
    chat_info = f"🆔 Chat ID: `{message.chat.id}`"

    if thread_id:
        chat_info += f"\n🧵 Thread ID: `{thread_id}`"

    await message.answer(chat_info, parse_mode="Markdown")

# Функція перевірки нових транзакцій
async def check_token_transactions():
    """Перевіряє нові транзакції у відстежуваних гаманцях"""
    while True:
        logger.info("🔍 Починаємо перевірку нових транзакцій...")

        watched_wallets = db.get_all_wallets()  # Отримуємо гаманці з БД
        for wallet in watched_wallets:
            wallet_address = wallet["address"]
            wallet_name = wallet["name"]
            transactions = get_token_transactions(wallet_address)

            if not isinstance(transactions, list):
                logger.error(f"❌ Помилка: get_token_transactions повернула не список для {wallet_address}. Отримано: {transactions}")
                continue

            if not transactions:
                logger.warning(f"⚠️ Не знайдено нових транзакцій для {wallet_address}")
                continue

            latest_tx = transactions[0]  # Остання транзакція
            tx_hash = latest_tx["hash"]
            token_out = latest_tx.get("token_out", "Невідомо")
            contract_address = latest_tx.get("token_out_address", "").lower()

            if db.is_transaction_exist(tx_hash):  # Перевіряємо, чи є транзакція в БД
                continue

            db.add_transaction(tx_hash, wallet_address, token_out, latest_tx.get("usd_value", "0"))

            thread_id = DEFAULT_THREAD_ID
            for token_name, config in TOKEN_CONFIG.items():
                if contract_address == config["contract_address"].lower():
                    thread_id = config["thread_id"]
                    logger.info(f"✅ Знайдено відповідність: {token_name} -> Тред {thread_id}")
                    break
            else:
                logger.warning(f"⚠️ Токен {token_out} ({contract_address}) не знайдено в мапінгу, відправляємо в {DEFAULT_THREAD_ID}")

            text, parse_mode = format_swap_message(
                tx_hash=tx_hash,
                sender=wallet_name,
                sender_url=f"https://arbiscan.io/address/{wallet_address}",
                amount_in=latest_tx.get("amount_in", "Невідомо"),
                token_in=latest_tx.get("token_in", "Невідомо"),
                token_in_url=f"https://arbiscan.io/token/{latest_tx.get('token_in_address', '')}",
                amount_out=latest_tx.get("amount_out", "Невідомо"),
                token_out=token_out,
                token_out_url=f"https://arbiscan.io/token/{latest_tx.get('token_out_address', '')}",
                usd_value=latest_tx.get("usd_value", "Невідомо")
            )

            try:
                logger.info(f"📩 Відправляємо повідомлення у тред {thread_id} для {wallet_address}...")
                await bot.send_message(
                    chat_id=CHAT_ID,
                    message_thread_id=thread_id,
                    text=text,
                    parse_mode=parse_mode,
                    disable_web_page_preview=True
                )
                logger.info(f"✅ Повідомлення надіслано у тред {thread_id}")
            except Exception as e:
                logger.error(f"❌ Помилка надсилання повідомлення: {str(e)}")

        await asyncio.sleep(CHECK_INTERVAL)  # Чекаємо перед наступною перевіркою

# Запуск бота
async def main():
    logger.info("🚀 Бот запущено та очікує нові транзакції!")
    asyncio.create_task(check_token_transactions())  # Запускаємо моніторинг транзакцій
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
