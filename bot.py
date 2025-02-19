import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from interface import register_handlers, get_main_menu, get_wallet_control_keyboard
from arbiscan import get_token_transactions
from message_formatter import format_swap_message
from database import Database
from threads_config import TOKEN_CONFIG, DEFAULT_THREAD_ID
from dotenv import load_dotenv
import os

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Логирование загрузки переменных окружения
try:
    logger.info("Загрузка переменных окружения:")
    logger.info(f"MYSQL_HOST: {os.getenv('MYSQL_HOST')}")
    logger.info(f"MYSQL_USER: {os.getenv('MYSQL_USER')}")
    logger.info(f"MYSQL_PASSWORD: {os.getenv('MYSQL_PASSWORD')}")
    logger.info(f"MYSQL_DATABASE: {os.getenv('MYSQL_DATABASE')}")
    logger.info(f"MYSQL_PORT: {os.getenv('MYSQL_PORT', 3306)}")
except Exception as e:
    print(f"Ошибка логирования: {e}")

# Инициализация бота, диспетчера и базы данных
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()
db = Database()

# Регистрация хендлеров
register_handlers(dp)

# Настройки
CHECK_INTERVAL = 2  # Проверка каждые 2 секунды
CHAT_ID = -1002458140371  # Chat ID группы

# Обработчик команды /start (главное меню)
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("✅ Бот запущен и мониторит транзакции!", reply_markup=get_main_menu())

# Функция проверки новых транзакций
async def check_token_transactions():
    """Проверяет новые транзакции в отслеживаемых кошельках"""
    while True:
        try:
            logger.info("🔍 Начинаем проверку новых транзакций...")

            watched_wallets = db.get_all_wallets()  # Получаем кошельки из БД
            for wallet in watched_wallets:
                wallet_address = wallet["address"]
                wallet_name = wallet["name"]
                transactions = get_token_transactions(wallet_address)

                if not isinstance(transactions, list):
                    logger.error(f"❌ Ошибка: get_token_transactions вернула не список для {wallet_address}. Получено: {transactions}")
                    continue

                if not transactions:
                    logger.warning(f"⚠️ Не найдено новых транзакций для {wallet_address}")
                    continue

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
                        logger.info(f"✅ Найдено соответствие: {token_name} -> Тред {thread_id}")
                        break
                else:
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
                    logger.info(f"📩 Отправляем сообщение в тред {thread_id} для {wallet_address}...")
                    await bot.send_message(
                        chat_id=CHAT_ID,
                        message_thread_id=thread_id,
                        text=text,
                        parse_mode=parse_mode,
                        disable_web_page_preview=True
                    )
                    logger.info(f"✅ Сообщение отправлено в тред {thread_id}")
                except Exception as e:
                    logger.error(f"❌ Ошибка отправки сообщения: {str(e)}")

        except Exception as e:
            logger.error(f"Произошла ошибка: {str(e)}")

        await asyncio.sleep(CHECK_INTERVAL)  # Ждем перед следующей проверкой

# Обработчик команды для редактирования кошельков
@dp.message(Command("EDITw"))
async def edit_wallet_command(message: types.Message):
    wallet_id = int(message.get_args().split('_')[1])
    wallet = db.get_wallet_by_id(wallet_id)
    if not wallet:
        await message.answer("❌ Кошелек не найден.")
        return

    text = f"Имя кошелька: {wallet['name']}\nАдрес кошелька: {wallet['address']}"
    await message.answer(text, reply_markup=get_wallet_control_keyboard(wallet_id))

# Функция для регистрации обработчиков команд и сообщений
def register_handlers(dp: Dispatcher):
    dp.message.register(start_command, Command("start"))
    dp.message.register(edit_wallet_command, Command("EDITw"))

# Запуск бота

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
