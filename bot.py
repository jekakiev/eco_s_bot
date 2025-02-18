import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import BOT_TOKEN
from arbiscan import get_transactions

# Ініціалізуємо бота та диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Тестовий гаманець
WATCHED_WALLET = "0x0CCe04C23E9e2D64759fc79BA728234Cff5d9A7f"
CHECK_INTERVAL = 10  # Кожні 10 секунд оновлення

# Обробник команди /start
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("✅ Бот запущено!")

# Функція перевірки нових транзакцій
async def check_transactions():
    last_tx_hash = None  # Зберігаємо останню транзакцію


    while True:
        transactions = get_transactions(WATCHED_WALLET)
        
        if isinstance(transactions, list) and transactions:
            latest_tx = transactions[0]  # Беремо останню транзакцію

            if last_tx_hash != latest_tx["hash"]:  # Якщо це нова транзакція
                last_tx_hash = latest_tx["hash"]
                text = f"🔔 Нова транзакція!

🔹 Hash: {latest_tx['hash']}
💰 Value: {int(latest_tx['value']) / 10**18} ETH
🔗 [Деталі](https://arbiscan.io/tx/{latest_tx['hash']})"
                
                # Надсилаємо сповіщення (тимчасово використовуємо chat_id = 123456789, заміни на свій)
                chat_id = 123456789  # Замінити на актуальний chat_id
                await bot.send_message(chat_id=chat_id, text=text, disable_web_page_preview=True)

        await asyncio.sleep(CHECK_INTERVAL)  # Затримка перед наступним запитом

# Запуск бота
async def main():
    asyncio.create_task(check_transactions())  # Запускаємо моніторинг транзакцій
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
