import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from interface import register_handlers, get_main_menu, get_wallet_control_keyboard
from arbiscan import get_token_transactions
from message_formatter import format_swap_message
from database import Database
from settings import BOT_TOKEN, CHECK_INTERVAL, CHAT_ID, LOG_TRANSACTIONS, LOG_SUCCESSFUL_TRANSACTIONS
from logger_config import logger

# Инициализация бота, диспетчера и базы данных
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db = Database()

# Регистрация хендлеров
register_handlers(dp)

# Обработчик команды /start (главное меню)
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("✅ Бот запущен и мониторит транзакции!", reply_markup=get_main_menu())
# Функция проверки новых транзакций
async def check_token_transactions():
    """Проверяет новые транзакции в отслеживаемых кошельках"""
    while True:
        try:
            if LOG_SUCCESSFUL_TRANSACTIONS:
                logger.info("🔍 Начинаем проверку новых транзакций...")

            watched_wallets = db.get_all_wallets()  # Получаем кошельки из БД
            for wallet in watched_wallets:
                wallet_address = wallet["address"]
                wallet_name = wallet["name"]
                transactions = get_token_transactions(wallet_address)

                if not isinstance(transactions, list):
                    if LOG_TRANSACTIONS:
                        logger.error(f"❌ Ошибка: get_token_transactions вернула не список для {wallet_address}. Получено: {len(transactions)} транзакций")
                    continue

                if not transactions:
                    if LOG_SUCCESSFUL_TRANSACTIONS:
                        logger.warning(f"⚠️ Не найдено новых транзакций для {wallet_address}")
                    continue

                if LOG_SUCCESSFUL_TRANSACTIONS:
                    logger.info(f"✅ Отримано {len(transactions)} транзакцій. Останній хеш: {transactions[0]['hash']}")

                latest_tx = transactions[0]  # Последняя транзакция
                tx_hash = latest_tx["hash"]
                token_out = latest_tx.get("token_out", "Неизвестно")
                contract_address = latest_tx.get("token_out_address", "").lower()

                if db.is_transaction_exist(tx_hash):  # Проверяем, существует ли транзакция в БД
                    continue

                db.add_transaction(tx_hash, wallet_address, token_out, latest_tx.get("usd_value", "0"))

                thread_id = DEFAULT_THREAD_ID
                for token_name, config in TOKEN_CONFIG.items():
                    if contract_address == config["contract_address"].lower():
                        thread_id = config["thread_id"]
                        if LOG_SUCCESSFUL_TRANSACTIONS:
                            logger.info(f"✅ Найдено соответствие: {token_name} -> Тред {thread_id}")
                        break
                else:
                    if LOG_SUCCESSFUL_TRANSACTIONS:
                        logger.warning(f"⚠️ Токен {token_out} ({contract_address}) не найден в маппинге, отправляем в {DEFAULT_THREAD_ID}")
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
                try:
                    if LOG_SUCCESSFUL_TRANSACTIONS:
                        logger.info(f"📩 Отправляем сообщение в тред {thread_id} для {wallet_address}...")
                    await bot.send_message(
                        chat_id=CHAT_ID,
                        message_thread_id=thread_id,
                        text=text,
                        parse_mode=parse_mode,
                        disable_web_page_preview=True
                    )
                    if LOG_SUCCESSFUL_TRANSACTIONS:
                        logger.info(f"✅ Сообщение отправлено в тред {thread_id}")
                except Exception as e:
                    logger.error(f"❌ Ошибка отправки сообщения: {str(e)}")

        except Exception as e:
            logger.error(f"Произошла ошибка: {str(e)}")

        await asyncio.sleep(CHECK_INTERVAL)  # Ждем перед следующей проверкой

# Обработчик команды для редактирования кошельков
@dp.message(Command(commands=["Edit"]))
async def edit_wallet_command(message: types.Message):
    if LOG_SUCCESSFUL_TRANSACTIONS:
        logger.info(f"Получена команда: {message.text}")
    try:
        short_address = message.text.split("_")[1]
        if LOG_SUCCESSFUL_TRANSACTIONS:
            logger.info(f"Получен короткий адрес: {short_address}")

        wallets = db.get_all_wallets()
        wallet = next((wallet for wallet in wallets if wallet["address"].endswith(short_address)), None)
        if not wallet:
            if LOG_SUCCESSFUL_TRANSACTIONS:
                logger.warning(f"Кошелек с адресом, оканчивающимся на {short_address}, не найден.")
            await message.answer("❌ Кошелек не найден.")
            return

        if LOG_SUCCESSFUL_TRANSACTIONS:
            logger.info(f"Найден кошелек: {wallet['name']} с адресом {wallet['address']}")
        text = f"Имя кошелька: {wallet['name']}\nАдрес кошелька: {wallet['address']}"
        await message.answer(text, reply_markup=get_wallet_control_keyboard(wallet['id']))
        if LOG_SUCCESSFUL_TRANSACTIONS:
            logger.info("Отправлено меню редактирования")
    except Exception as e:
        logger.error(f"Ошибка обработки команды Edit: {e}")

# Функция для регистрации обработчиков команд и сообщений
def register_handlers(dp: Dispatcher):
    dp.message.register(start_command, Command("start"))
    dp.message.register(edit_wallet_command, Command("Edit"))

# Запуск бота
async def main():
    try:
        logger.info("🚀 Бот запущен и ждет новые транзакции!")
        asyncio.create_task(check_token_transactions())  # Запускаем мониторинг транзакций
        await dp.start_polling(bot)
    except Exception as e:
        print(f"Ошибка запуска бота: {e}")

if __name__ == "__main__":
    asyncio.run(main())
