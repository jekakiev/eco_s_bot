import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import BOT_TOKEN
from arbiscan import get_token_transactions  # Імпортуємо правильну функцію

# Ініціалізуємо бота та диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Тестовий гаманець
WATCHED_WALLET = "0x0CCe04C23E9e2D64759fc79BA728234Cff5d9A7f"
CHECK_INTERVAL = 10  # Оновлення кожні 10 секунд
THREAD_ID = 7  # Вставлений Thread ID гілки
CHAT_ID = -1002458140371  # Встав свій Chat ID

# Обробник команди /start
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("✅ Бот запущено!")

# Обробник команди /get_chat_id (Отримання ID гілки)
@dp.message(Command("get_chat_id"))
async def get_chat_id(message: types.Message):
    thread_id = message.message_thread_id  # ID треда (гілки)
    chat_info = f"🆔 Chat ID: `{message.chat.id}`"

    if thread_id:
        chat_info += f"\n🧵 Thread ID: `{thread_id}`"

    await message.answer(chat_info, parse_mode="Markdown")

# Функція перевірки нових транзакцій конкретного токена
async def check_token_transactions():
    last_tx_hash = None  # Зберігаємо останню транзакцію

    while True:
        transactions = get_token_transactions(WATCHED_WALLET)

        if isinstance(transactions, list) and transactions:
            latest_tx = transactions[0]  # Беремо останню транзакцію

            if last_tx_hash != latest_tx["hash"]:  # Якщо це нова транзакція
                last_tx_hash = latest_tx["hash"]

                text = (
                    f"🔔 Нова транзакція токена!\n\n"
                    f"🔹 Hash: {latest_tx['hash']}\n"
                    f"💰 Value: {int(latest_tx['value']) / 10**18} {latest_tx['tokenSymbol']}\n"
                    f"📤 Відправник: {latest_tx['from']}\n"
                    f"📥 Одержувач: {latest_tx['to']}\n"
                    f"🔗 [Деталі](https://arbiscan.io/tx/{latest_tx['hash']})"
                )

                await bot.send_message(chat_id=CHAT_ID, message_thread_id=THREAD_ID, text=text, disable_web_page_preview=True)

        await asyncio.sleep(CHECK_INTERVAL)  # Затримка перед наступним запитом

# Запуск бота
async def main():
    asyncio.create_task(check_token_transactions())  # Запускаємо моніторинг транзакцій токена
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
