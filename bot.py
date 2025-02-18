import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import BOT_TOKEN
from arbiscan import get_token_transactions  # Функция получения транзакций
from message_formatter import format_swap_message  # Форматирование сообщений
from wallets_config import WATCHED_WALLETS  # Загружаем настройки кошельков
from threads_config import TOKEN_CONFIG, DEFAULT_THREAD_ID  # Мапінг тредів

# Ініціалізуємо бота та диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Налаштування
CHECK_INTERVAL = 10  # Перевірка кожні 10 секунд
CHAT_ID = -1002458140371  # Chat ID групи

# Обробник команди /start
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("✅ Бот запущен!")

# Обробник команди /get_chat_id (Отримання ID треда)
@dp.message(Command("get_chat_id"))
async def get_chat_id(message: types.Message):
    thread_id = message.message_thread_id  # ID треда (гілки)
    chat_info = f"🆔 Chat ID: `{message.chat.id}`"

    if thread_id:
        chat_info += f"\n🧵 Thread ID: `{thread_id}`"

    await message.answer(chat_info, parse_mode="Markdown")

# Функція перевірки нових транзакцій конкретного токена
async def check_token_transactions():
    last_tx_hash = {}  # Зберігаємо останні транзакції для кожного гаманця

    while True:
        for wallet_address, wallet_name in WATCHED_WALLETS.items():
            transactions = get_token_transactions(wallet_address)

            if isinstance(transactions, list) and transactions:
                latest_tx = transactions[0]  # Беремо останню транзакцію

                if last_tx_hash.get(wallet_address) != latest_tx["hash"]:  # Якщо це нова транзакція
                    last_tx_hash[wallet_address] = latest_tx["hash"]

                    # Отримуємо інформацію про токен
                    token_name = latest_tx.get("token_in", "Невідомий токен")
                    thread_id = TOKEN_THREADS.get(token_name, DEFAULT_THREAD_ID)  # Вибираємо тред

                    text, parse_mode = format_swap_message(
                        tx_hash=latest_tx["hash"],
                        sender=wallet_name,  # Використовуємо ім'я гаманця
                        sender_url=f"https://arbiscan.io/address/{wallet_address}",
                        amount_in=latest_tx.get("amount_in", "Неизвестно"),
                        token_in=token_name,
                        token_in_url=f"https://arbiscan.io/token/{latest_tx.get('token_in_address', '')}",
                        amount_out=latest_tx.get("amount_out", "Неизвестно"),
                        token_out=latest_tx.get("token_out", "Неизвестно"),
                        token_out_url=f"https://arbiscan.io/token/{latest_tx.get('token_out_address', '')}",
                        usd_value=latest_tx.get("usd_value", "Неизвестно")
                    )

                    # Відправляємо повідомлення в відповідний тред
                    await bot.send_message(
                        chat_id=CHAT_ID,
                        message_thread_id=thread_id,
                        text=text,
                        parse_mode=parse_mode,
                        disable_web_page_preview=True
                    )

        await asyncio.sleep(CHECK_INTERVAL)  # Затримка перед наступним запитом

# Запуск бота
async def main():
    asyncio.create_task(check_token_transactions())  # Запускаємо моніторинг транзакцій токенів
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
