import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import BOT_TOKEN
from arbiscan import get_token_transactions  # Функція отримання транзакцій
from message_formatter import format_swap_message  # Форматування повідомлень
from wallets_config import WATCHED_WALLETS  # Адреси гаманців
from threads_config import TOKEN_CONFIG, DEFAULT_THREAD_ID  # Налаштування тредів

# Налаштовуємо логування
logging.basicConfig(level=logging.INFO)

# Ініціалізація бота і диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Налаштування
CHECK_INTERVAL = 10  # Перевірка кожні 10 секунд
CHAT_ID = -1002458140371  # Chat ID групи

# Обробник команди /start
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("✅ Бот запущений!")

# Функція перевірки нових транзакцій конкретного токена
async def check_token_transactions():
    last_tx_hash = {}  # Зберігаємо останні транзакції для кожного гаманця

    while True:
        for wallet_address, wallet_name in WATCHED_WALLETS.items():
            transactions = get_token_transactions(wallet_address)

            if isinstance(transactions, list) and transactions:
                latest_tx = transactions[0]  # Беремо останню транзакцію

                # Перевіряємо, чи ця транзакція нова
                if last_tx_hash.get(wallet_address) == latest_tx["hash"]:
                    logging.info(f"🔄 Транзакція {latest_tx['hash']} вже була оброблена, пропускаємо.")
                    continue  # Пропускаємо, якщо це та ж сама транзакція

                last_tx_hash[wallet_address] = latest_tx["hash"]

                token_name = latest_tx.get("token_in", "Невідомий токен")
                token_data = TOKEN_CONFIG.get(token_name, {})
                thread_id = token_data.get("thread_id", DEFAULT_THREAD_ID)

                logging.info(f"📩 Нова транзакція {latest_tx['hash']} для токена {token_name} -> Тред {thread_id}")

                # Формуємо повідомлення
                text, parse_mode = format_swap_message(
                    tx_hash=latest_tx["hash"],
                    sender=wallet_name,  # Використовуємо ім'я гаманця
                    sender_url=f"https://arbiscan.io/address/{wallet_address}",
                    amount_in=latest_tx.get("amount_in", 0),
                    token_in=latest_tx.get("token_in", "Невідомо"),
                    token_in_url=f"https://arbiscan.io/token/{latest_tx.get('token_in_address', '')}",
                    amount_out=latest_tx.get("amount_out", 0),
                    token_out=latest_tx.get("token_out", "Невідомо"),
                    token_out_url=f"https://arbiscan.io/token/{latest_tx.get('token_out_address', '')}",
                    usd_value=latest_tx.get("usd_value", "Невідомо")
                )

                # Відправляємо повідомлення в Telegram
                try:
                    await bot.send_message(
                        chat_id=CHAT_ID, 
                        message_thread_id=thread_id, 
                        text=text, 
                        parse_mode=parse_mode, 
                        disable_web_page_preview=True
                    )
                    logging.info(f"✅ Повідомлення надіслано у тред {thread_id}: {latest_tx['hash']}")
                except Exception as e:
                    logging.error(f"❌ ПОМИЛКА відправки повідомлення: {str(e)}")

        await asyncio.sleep(CHECK_INTERVAL)  # Затримка перед наступним запитом

# Запуск бота
async def main():
    logging.info("🚀 Бот запущено!")
    asyncio.create_task(check_token_transactions())  # Запускаємо моніторинг транзакцій
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
