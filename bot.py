import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import BOT_TOKEN
from arbiscan import get_token_transactions  # Функция получения транзакций
from message_formatter import format_swap_message  # Форматирование сообщений
from wallets_config import WATCHED_WALLETS  # Загружаем настройки кошельков

# Инициализируем бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Настройки
CHECK_INTERVAL = 10  # Проверка каждые 10 секунд
THREAD_ID = 7  # Thread ID треда
CHAT_ID = -1002458140371  # Chat ID группы

# Обработчик команды /start
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("✅ Бот запущен!")

# Обработчик команды /get_chat_id (Получение ID треда)
@dp.message(Command("get_chat_id"))
async def get_chat_id(message: types.Message):
    thread_id = message.message_thread_id  # ID треда (ветки)
    chat_info = f"🆔 Chat ID: `{message.chat.id}`"

    if thread_id:
        chat_info += f"\n🧵 Thread ID: `{thread_id}`"

    await message.answer(chat_info, parse_mode="Markdown")

# Функция проверки новых транзакций конкретного токена
async def check_token_transactions():
    last_tx_hash = {}  # Сохраняем последние транзакции для каждого кошелька

    while True:
        for wallet_address, wallet_name in WATCHED_WALLETS.items():
            transactions = get_token_transactions(wallet_address)

            if isinstance(transactions, list) and transactions:
                latest_tx = transactions[0]  # Берем последнюю транзакцию

                if last_tx_hash.get(wallet_address) != latest_tx["hash"]:  # Если это новая транзакция
                    last_tx_hash[wallet_address] = latest_tx["hash"]

                    text = format_swap_message(
                        tx_hash=latest_tx["hash"],
                        sender=wallet_name,  # Используем имя кошелька
                        sender_url=f"https://arbiscan.io/address/{wallet_address}",
                        amount_in=latest_tx.get("amount_in", "Неизвестно"),
                        token_in=latest_tx.get("token_in", "Неизвестно"),
                        token_in_url=f"https://arbiscan.io/token/{latest_tx.get('token_in_address', '')}",
                        amount_out=latest_tx.get("amount_out", "Неизвестно"),
                        token_out=latest_tx.get("token_out", "Неизвестно"),
                        token_out_url=f"https://arbiscan.io/token/{latest_tx.get('token_out_address', '')}",
                        usd_value=latest_tx.get("usd_value", "Неизвестно")
                    )

                    await bot.send_message(chat_id=CHAT_ID, message_thread_id=THREAD_ID, text=text, disable_web_page_preview=True)

        await asyncio.sleep(CHECK_INTERVAL)  # Задержка перед следующим запросом

# Запуск бота
async def main():
    asyncio.create_task(check_token_transactions())  # Запускаем мониторинг транзакций токенов
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
