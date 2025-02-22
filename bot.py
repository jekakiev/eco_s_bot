import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from interface import register_handlers, get_main_menu
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

                if not isinstance(transactions, dict):  # Исправлено с list на dict, так как get_token_transactions возвращает словарь
                    if LOG_TRANSACTIONS:
                        logger.error(f"❌ Ошибка: get_token_transactions вернула не словарь для {wallet_address}. Получено: {type(transactions)}")
                    continue

                if not transactions:
                    if LOG_SUCCESSFUL_TRANSACTIONS:
                        logger.warning(f"⚠️ Не найдено новых транзакций для {wallet_address}")
                    continue

                logger.info(f"LOG_SUCCESSFUL_TRANSACTIONS: {LOG_SUCCESSFUL_TRANSACTIONS}")
                if LOG_SUCCESSFUL_TRANSACTIONS:
                    logger.info(f"✅ Получено {len(transactions)} уникальных транзакций для {wallet_address}")

                for tx_hash, tx_list in transactions.items():
                    latest_tx = tx_list[0]  # Первая запись для данного хеша
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

# Запуск бота
async def main():
    try:
        logger.info("🚀 Бот запущен и ждет новые транзакции!")
        asyncio.create_task(check_token_transactions())  # Запускаем мониторинг транзакций
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")

if __name__ == "__main__":
    asyncio.run(main())