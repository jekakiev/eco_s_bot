import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import BOT_TOKEN
from arbiscan import get_token_transactions  # Функція отримання транзакцій
from message_formatter import format_swap_message  # Форматування повідомлень
from wallets_config import WATCHED_WALLETS  # Гаманці
from threads_config import TOKEN_CONFIG, DEFAULT_THREAD_ID  # Мапінг токенів і тредів
from logger_config import logger  # Наш логер

# Ініціалізація бота і диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Налаштування
CHECK_INTERVAL = 10  # Перевірка кожні 10 секунд
CHAT_ID = -1002458140371  # Chat ID групи

# Останні хеші транзакцій
last_tx_hash = {}

# Функція перевірки нових транзакцій
async def check_token_transactions():
    global last_tx_hash

    while True:
        logger.info("🔍 Починаємо перевірку нових транзакцій...")
        
        for wallet_address, wallet_name in WATCHED_WALLETS.items():
            transactions = get_token_transactions(wallet_address)
            
            if not isinstance(transactions, list) or not transactions:
                logger.warning(f"⚠️ Не знайдено транзакцій для {wallet_address}")
                continue
            
            for tx in transactions:
                tx_hash = tx["hash"]

                # Логуємо кожну транзакцію перед перевіркою
                logger.info(f"📡 Отримана транзакція {tx_hash} для {wallet_name}")

                if last_tx_hash.get(wallet_address) == tx_hash:
                    logger.info(f"🔄 Транзакція {tx_hash} вже була оброблена, пропускаємо.")
                    continue

                # Зберігаємо новий останній хеш транзакції
                last_tx_hash[wallet_address] = tx_hash

                token_name = tx.get("token_in", "Невідомий токен")
                token_data = TOKEN_CONFIG.get(token_name, {})

                if not token_data:
                    logger.warning(f"⚠️ Токен {token_name} не знайдено у мапінгу, використовуємо DEFAULT_THREAD_ID")
                
                thread_id = token_data.get("thread_id", DEFAULT_THREAD_ID)

                logger.info(f"📩 Готуємо повідомлення для токена {token_name} у тред {thread_id}")

                # Формуємо повідомлення
                text, parse_mode = format_swap_message(
                    tx_hash=tx_hash,
                    sender=wallet_name,
                    sender_url=f"https://arbiscan.io/address/{wallet_address}",
                    amount_in=tx.get("amount_in", 0),
                    token_in=tx.get("token_in", "Невідомо"),
                    token_in_url=f"https://arbiscan.io/token/{tx.get('token_in_address', '')}",
                    amount_out=tx.get("amount_out", 0),
                    token_out=tx.get("token_out", "Невідомо"),
                    token_out_url=f"https://arbiscan.io/token/{tx.get('token_out_address', '')}",
                    usd_value=tx.get("usd_value", "Невідомо")
                )

                # Відправляємо повідомлення
                try:
                    logger.info(f"📤 Надсилаємо повідомлення у тред {thread_id}...")
                    await bot.send_message(
                        chat_id=CHAT_ID, 
                        message_thread_id=thread_id, 
                        text=text, 
                        parse_mode=parse_mode, 
                        disable_web_page_preview=True
                    )
                    logger.info(f"✅ Повідомлення успішно відправлено для {token_name} у тред {thread_id}")
                except Exception as e:
                    logger.error(f"❌ ПОМИЛКА відправки повідомлення: {str(e)}")

        logger.info("⏳ Чекаємо наступний цикл перевірки...")
        await asyncio.sleep(CHECK_INTERVAL)

# Запуск бота
async def main():
    logger.info("🚀 Бот запущено!")
    asyncio.create_task(check_token_transactions())  # Запускаємо моніторинг транзакцій
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
