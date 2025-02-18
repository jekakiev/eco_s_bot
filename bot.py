import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import BOT_TOKEN
from arbiscan import get_token_transactions  # Функція отримання транзакцій
from message_formatter import format_swap_message  # Форматування повідомлень
from wallets_config import WATCHED_WALLETS  # Налаштування відстежуваних гаманців
from threads_config import TOKEN_CONFIG, DEFAULT_THREAD_ID  # Мапінг тредів

# Ініціалізуємо бота та диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Налаштування
CHECK_INTERVAL = 10  # Перевірка кожні 10 секунд
CHAT_ID = -1002458140371  # ID групи

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def start_command(message: types.Message):
    """Обробник команди /start"""
    await message.answer("✅ Бот запущено!")
    logger.info("Бот успішно запущено!")

async def get_chat_id(message: types.Message):
    """Обробник команди /get_chat_id"""
    thread_id = message.message_thread_id  # ID треда
    chat_info = f"🆔 Chat ID: `{message.chat.id}`"

    if thread_id:
        chat_info += f"\n🧵 Thread ID: `{thread_id}`"

    await message.answer(chat_info, parse_mode="Markdown")

async def check_token_transactions():
    """Перевіряє нові транзакції у відстежуваних гаманцях"""
    last_tx_hash = {}

    while True:
        logger.info("🔍 Починаємо перевірку нових транзакцій...")
        for wallet_address, wallet_name in WATCHED_WALLETS.items():
            transactions = get_token_transactions(wallet_address)

            if not transactions:
                logger.warning(f"⚠️ Не знайдено транзакцій для {wallet_address}")
                continue

            latest_tx = transactions[0]  # Остання транзакція
            tx_hash = latest_tx["hash"]
            token_out = latest_tx.get("token_out", "Невідомо")
            contract_address = latest_tx.get("token_out_address", "").lower()

            # Логуємо отримані транзакції
            logger.info(f"🔄 Отримано транзакцію: {tx_hash}")
            logger.info(f"📌 Контрактна адреса токена: {contract_address}")
            logger.info(f"📌 Токен: {token_out}")

            if last_tx_hash.get(wallet_address) == tx_hash:
                continue  # Якщо транзакція вже була оброблена

            last_tx_hash[wallet_address] = tx_hash

            thread_id = DEFAULT_THREAD_ID

            # Знаходимо відповідний тред для контрактної адреси токена
            for token_name, config in TOKEN_CONFIG.items():
                if contract_address == config["contract_address"].lower():
                    thread_id = config["thread_id"]
                    logger.info(f"✅ Знайдено відповідність: {token_name} -> Тред {thread_id}")
                    break
            else:
                logger.warning(f"⚠️ Токен {token_out} ({contract_address}) не знайдено в мапінгу, відправляємо в {DEFAULT_THREAD_ID}")

            # Форматуємо повідомлення
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

            # Відправляємо повідомлення у відповідний тред
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

async def main():
    """Запуск бота"""
    dp.message.register(start_command, Command("start"))
    dp.message.register(get_chat_id, Command("get_chat_id"))

    asyncio.create_task(check_token_transactions())  # Запускаємо перевірку транзакцій
    logger.info("🚀 Бот запущено та очікує нові транзакції!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
