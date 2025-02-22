import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from interface import register_handlers, get_main_menu
from arbiscan import get_token_transactions
from message_formatter import format_swap_message
from database import Database
from settings import BOT_TOKEN, CHAT_ID, DEFAULT_THREAD_ID
from logger_config import logger, update_log_settings
import time

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db = Database()

# Загружаем настройки из базы
settings = db.get_all_settings()
CHECK_INTERVAL = int(settings.get("CHECK_INTERVAL", "10"))
LOG_TRANSACTIONS = int(settings.get("LOG_TRANSACTIONS", "0"))
LOG_SUCCESSFUL_TRANSACTIONS = int(settings.get("LOG_SUCCESSFUL_TRANSACTIONS", "0"))
SEND_LAST_TRANSACTION = int(settings.get("SEND_LAST_TRANSACTION", "0"))

logger.info("Статус логов и настроек при запуске бота:")
logger.info(f"- Логи транзакций: {'Включены' if LOG_TRANSACTIONS else 'Выключены'}")
logger.info(f"- Логи успешных транзакций: {'Включены' if LOG_SUCCESSFUL_TRANSACTIONS else 'Выключены'}")
logger.info(f"- Отправка последней транзакции: {'Включена' if SEND_LAST_TRANSACTION else 'Выключена'}")

# Логируем текущие значения из базы для отладки
logger.debug(f"Загруженные настройки из базы: CHECK_INTERVAL={CHECK_INTERVAL}, LOG_TRANSACTIONS={LOG_TRANSACTIONS}, LOG_SUCCESSFUL_TRANSACTIONS={LOG_SUCCESSFUL_TRANSACTIONS}, SEND_LAST_TRANSACTION={SEND_LAST_TRANSACTION}")

register_handlers(dp)

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("✅ Бот запущен и мониторит транзакции!", reply_markup=get_main_menu())
    if LOG_SUCCESSFUL_TRANSACTIONS:
        logger.info("Команда /start была обработана успешно (тестовое сообщение для успешных логов)")

@dp.message(Command("get_last_transaction"))
async def get_last_transaction_command(message: types.Message):
    last_transaction = db.get_last_transaction()
    if last_transaction:
        logger.debug(f"Данные последней транзакции по запросу: {last_transaction}")
        wallet = db.get_wallet_by_address(last_transaction['wallet_address'])
        wallet_name = wallet['name'] if wallet else last_transaction['wallet_address']
        tracked_tokens = {t["contract_address"].lower(): t for t in db.get_all_tracked_tokens()}  # Приводим к нижнему регистру
        thread_id = DEFAULT_THREAD_ID  # Дефолтный тред
        contract_address = last_transaction.get('token_name', '').lower()  # Используем token_name как временное решение, если contract_address отсутствует
        logger.debug(f"Проверка токена для транзакции: token_name={last_transaction['token_name']}, contract_address={contract_address}, tracked_tokens={tracked_tokens}")

        if contract_address in tracked_tokens:
            thread_id = tracked_tokens[contract_address]["thread_id"]
            logger.debug(f"Найден токен в tracked_tokens, thread_id={thread_id}")
        else:
            logger.warning(f"Токен {contract_address} не найден в tracked_tokens, используется дефолтный тред {thread_id}")

        text, parse_mode = format_swap_message(
            tx_hash=last_transaction['tx_hash'],
            sender=wallet_name,
            sender_url=f"https://arbiscan.io/address/{last_transaction['wallet_address']}",
            amount_in="Неизвестно",  # Пока оставим, так как точные суммы нужно уточнить
            token_in=last_transaction['token_name'],
            token_in_url=f"https://arbiscan.io/token/{last_transaction['token_name']}",  # Уточнить контракт
            amount_out="Неизвестно",
            token_out=last_transaction['token_name'],
            token_out_url=f"https://arbiscan.io/token/{last_transaction['token_name']}",  # Уточнить контракт
            usd_value=last_transaction['usd_value']
        )

        await bot.send_message(
            chat_id=CHAT_ID,
            message_thread_id=thread_id,
            text=text,
            parse_mode=parse_mode,
            disable_web_page_preview=True
        )
    else:
        await message.answer("Нет записей о транзакциях.", disable_web_page_preview=True)
    if LOG_SUCCESSFUL_TRANSACTIONS:
        logger.info(f"Команда /get_last_transaction была обработана успешно для чата {message.chat.id} (тестовое сообщение для успешных логов)")

@dp.message(Command("get_thread_id"))
async def get_thread_id_command(message: types.Message):
    thread_id = message.message_thread_id if message.is_topic_message else "Нет треда (основной чат)"
    await message.answer(f"ID текущего треда: `{thread_id}`", parse_mode="Markdown")
    if LOG_SUCCESSFUL_TRANSACTIONS:
        logger.info(f"Команда /get_thread_id была обработана успешно для чата {message.chat.id} (тестовое сообщение для успешных логов)")

async def check_token_transactions():
    while True:
        start_time = time.time()
        try:
            watched_wallets = db.get_all_wallets()
            tracked_tokens = {t["contract_address"].lower(): t for t in db.get_all_tracked_tokens()}  # Приводим к нижнему регистру
            default_thread_id = DEFAULT_THREAD_ID  # Базовый тред, если токен не отслеживается

            # Логируем начало проверки, если LOG_TRANSACTIONS включён
            if LOG_TRANSACTIONS:
                logger.info(f"Начинаем проверку новых транзакций. Количество кошельков для проверки: {len(watched_wallets)}")

            # Получаем транзакции для всех кошельков одним запросом
            wallet_addresses = [wallet["address"] for wallet in watched_wallets]
            # Ограничиваем количество адресов, чтобы не превышать лимит Arbiscan (5 адресов)
            max_addresses_per_request = 5
            all_transactions = {}
            for i in range(0, len(wallet_addresses), max_addresses_per_request):
                chunk_addresses = wallet_addresses[i:i + max_addresses_per_request]
                transactions = get_token_transactions(chunk_addresses)
                all_transactions.update(transactions)

            new_transactions_count = 0
            for wallet_address, tx_list in all_transactions.items():
                wallet = next((w for w in watched_wallets if w["address"] == wallet_address), None)
                if not wallet:
                    continue

                wallet_name = wallet["name"]
                for tx in tx_list:
                    tx_hash = tx.get("tx_hash", "")
                    token_out = tx.get("token_out", "Неизвестно")
                    contract_address = tx.get("token_out_address", "").lower()  # Приводим к нижнему регистру

                    if not db.is_transaction_exist(tx_hash):
                        db.add_transaction(tx_hash, wallet_address, token_out, tx.get("usd_value", "0"))
                        new_transactions_count += 1

                        # Определяем тред для отправки сообщения
                        thread_id = default_thread_id
                        logger.debug(f"Проверка токена для транзакции: token_out={token_out}, contract_address={contract_address}, tracked_tokens={tracked_tokens}")

                        if contract_address in tracked_tokens:
                            thread_id = tracked_tokens[contract_address]["thread_id"]
                            logger.debug(f"Найден токен в tracked_tokens, thread_id={thread_id}")
                        else:
                            logger.warning(f"Токен {contract_address} не найден в tracked_tokens, используется дефолтный тред {thread_id}")

                        text, parse_mode = format_swap_message(
                            tx_hash=tx_hash,
                            sender=wallet_name,
                            sender_url=f"https://arbiscan.io/address/{wallet_address}",
                            amount_in=tx.get("amount_in", "Неизвестно"),
                            token_in=tx.get("token_in", "Неизвестно"),
                            token_in_url=f"https://arbiscan.io/token/{tx.get('token_in_address', '')}",
                            amount_out=tx.get("amount_out", "Неизвестно"),
                            token_out=token_out,
                            token_out_url=f"https://arbiscan.io/token/{tx.get('token_out_address', '')}",
                            usd_value=tx.get("usd_value", "Неизвестно")
                        )

                        if text.startswith("Ошибка"):
                            logger.error(f"Ошибка форматирования сообщения для транзакции {tx_hash}: {text}")
                            continue

                        if LOG_SUCCESSFUL_TRANSACTIONS:
                            logger.info(f"Кошелёк '{wallet_name}' обнаружено {new_transactions_count} новых транзакций, сообщение отправлено в тред с ID {thread_id}")

                        await bot.send_message(
                            chat_id=CHAT_ID,
                            message_thread_id=thread_id,
                            text=text,
                            parse_mode=parse_mode,
                            disable_web_page_preview=True
                        )

            # Отправка последней транзакции в тред, если настройка включена
            if SEND_LAST_TRANSACTION:
                last_transaction = db.get_last_transaction()
                if last_transaction:
                    wallet = db.get_wallet_by_address(last_transaction['wallet_address'])
                    wallet_name = wallet['name'] if wallet else last_transaction['wallet_address']
                    tracked_tokens = {t["contract_address"].lower(): t for t in db.get_all_tracked_tokens()}  # Приводим к нижнему регистру
                    thread_id = DEFAULT_THREAD_ID  # Дефолтный тред
                    contract_address = last_transaction.get('token_name', '').lower()  # Используем token_name как временное решение
                    logger.debug(f"Проверка токена для последней транзакции: token_name={last_transaction['token_name']}, contract_address={contract_address}, tracked_tokens={tracked_tokens}")

                    if contract_address in tracked_tokens:
                        thread_id = tracked_tokens[contract_address]["thread_id"]
                        logger.debug(f"Найден токен в tracked_tokens для последней транзакции, thread_id={thread_id}")
                    else:
                        logger.warning(f"Токен {contract_address} не найден в tracked_tokens для последней транзакции, используется дефолтный тред {thread_id}")

                    text, parse_mode = format_swap_message(
                        tx_hash=last_transaction['tx_hash'],
                        sender=wallet_name,
                        sender_url=f"https://arbiscan.io/address/{last_transaction['wallet_address']}",
                        amount_in="Неизвестно",  # Пока оставим, так как точные суммы нужно уточнить
                        token_in=last_transaction['token_name'],
                        token_in_url=f"https://arbiscan.io/token/{last_transaction['token_name']}",  # Уточнить контракт
                        amount_out="Неизвестно",
                        token_out=last_transaction['token_name'],
                        token_out_url=f"https://arbiscan.io/token/{last_transaction['token_name']}",  # Уточнить контракт
                        usd_value=last_transaction['usd_value']
                    )

                    if not text.startswith("Ошибка"):
                        logger.debug(f"Попытка отправки последней транзакции в тред {thread_id}: {text}")
                        try:
                            await bot.send_message(
                                chat_id=CHAT_ID,
                                message_thread_id=thread_id,
                                text=text,
                                parse_mode=parse_mode,
                                disable_web_page_preview=True
                            )
                            if LOG_SUCCESSFUL_TRANSACTIONS:
                                logger.info(f"Отправлена последняя транзакция в тред с ID {thread_id}")
                        except Exception as e:
                            logger.error(f"Ошибка при отправке последней транзакции: {str(e)}")
                    else:
                        logger.error(f"Ошибка форматирования последней транзакции: {text}")
                else:
                    logger.debug("Нет последней транзакции для отправки")

            # Логируем время обработки и количество проверенных кошельков, если LOG_TRANSACTIONS включён
            if LOG_TRANSACTIONS:
                logger.info(f"Проверка транзакций завершена. Время обработки: {time.time() - start_time:.2f} сек. Количество проверенных кошельков: {len(watched_wallets)}")

        except Exception as e:
            logger.error(f"Произошла ошибка: {str(e)}")

        await asyncio.sleep(CHECK_INTERVAL)

async def main():
    logger.info("🚀 Бот запущен и ждет новые транзакции!")
    asyncio.create_task(check_token_transactions())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())