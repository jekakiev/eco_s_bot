import asyncio
import time
from database import Database
from utils.arbiscan import get_token_transactions
from utils.message_formatter import format_swap_message
from send_message import send_message
from config.settings import DEFAULT_THREAD_ID
from utils.logger_config import logger

db = Database()

async def check_token_transactions(bot, chat_id):
    last_sent_transaction_hash = None  # Отслеживаем последнюю отправленную транзакцию
    while True:
        start_time = time.time()
        try:
            # Перечитываем настройки в каждом цикле
            check_interval = int(db.get_setting("CHECK_INTERVAL") or 10)
            send_last_transaction = int(db.get_setting("SEND_LAST_TRANSACTION") or 0)
            transaction_info = int(db.get_setting("TRANSACTION_INFO") or 0)
            debug = int(db.get_setting("DEBUG") or 0)

            watched_wallets = db.get_all_wallets()
            tracked_tokens = {t["contract_address"].lower(): t for t in db.get_all_tracked_tokens()}
            default_thread_id = DEFAULT_THREAD_ID

            if transaction_info:
                logger.info(f"Начинаем проверку новых транзакций. Количество кошельков: {len(watched_wallets)}")

            wallet_addresses = [wallet["address"] for wallet in watched_wallets]
            all_transactions = await get_token_transactions(wallet_addresses)

            new_transactions_count = 0
            for wallet_address, tx_list in all_transactions.items():
                wallet = next((w for w in watched_wallets if w["address"] == wallet_address), None)
                if not wallet:
                    continue

                wallet_name = wallet["name"]
                for tx in tx_list:
                    tx_hash = tx.get("tx_hash", "")
                    token_out = tx.get("token_out", "Неизвестно")
                    contract_address = tx.get("token_out_address", "").lower()

                    if contract_address and not contract_address.startswith("0x"):
                        contract_address = "0x" + contract_address

                    if not db.is_transaction_exist(tx_hash):
                        db.add_transaction(tx_hash, wallet_address, token_out, tx.get("usd_value", "0"))
                        new_transactions_count += 1

                        thread_id = default_thread_id
                        if contract_address in tracked_tokens:
                            thread_id = tracked_tokens[contract_address]["thread_id"]
                            if debug:
                                logger.debug(f"Найден токен: thread_id={thread_id}")
                        else:
                            if debug:
                                logger.warning(f"Contract_address {contract_address} не найден, использую {thread_id}")

                        text, parse_mode = format_swap_message(
                            tx_hash=tx_hash,
                            sender=wallet_name,
                            sender_url=f"https://arbiscan.io/address/{wallet_address}",
                            amount_in=tx.get('amount_in', 'Неизвестно'),
                            token_in=tx.get('token_in', 'Неизвестно'),
                            token_in_url=tx.get('token_in_url', ''),
                            amount_out=tx.get('amount_out', 'Неизвестно'),
                            token_out=tx.get('token_out', 'Неизвестно'),
                            token_out_url=tx.get('token_out_url', ''),
                            usd_value=tx.get('usd_value', '0')
                        )

                        if text.startswith("Ошибка"):
                            if int(db.get_setting("API_ERRORS") or 1):
                                logger.error(f"Ошибка форматирования: {text}")
                            continue

                        try:
                            await send_message(chat_id, thread_id, text, parse_mode=parse_mode)
                            if transaction_info:
                                logger.info(f"Сообщение отправлено в тред {thread_id}")
                        except Exception as e:
                            if int(db.get_setting("API_ERRORS") or 1):
                                logger.error(f"Ошибка отправки: {str(e)}")

            if send_last_transaction:
                last_transaction = db.get_last_transaction()
                if last_transaction and last_transaction['tx_hash'] != last_sent_transaction_hash:
                    wallet = db.get_wallet_by_address(last_transaction['wallet_address'])
                    wallet_name = wallet['name'] if wallet else last_transaction['wallet_address']
                    contract_address = last_transaction.get('token_out_address', '').lower()

                    thread_id = default_thread_id
                    if contract_address in tracked_tokens:
                        thread_id = tracked_tokens[contract_address]["thread_id"]

                    text, parse_mode = format_swap_message(
                        tx_hash=last_transaction['tx_hash'],
                        sender=wallet_name,
                        sender_url=f"https://arbiscan.io/address/{last_transaction['wallet_address']}",
                        amount_in=last_transaction.get('amount_in', 'Неизвестно'),
                        token_in=last_transaction.get('token_in', 'Неизвестно'),
                        token_in_url=last_transaction.get('token_in_url', ''),
                        amount_out=last_transaction.get('amount_out', 'Неизвестно'),
                        token_out=last_transaction.get('token_out', 'Неизвестно'),
                        token_out_url=last_transaction.get('token_out_url', ''),
                        usd_value=last_transaction.get('usd_value', '0')
                    )

                    if not text.startswith("Ошибка"):
                        try:
                            await send_message(chat_id, thread_id, text, parse_mode=parse_mode)
                            last_sent_transaction_hash = last_transaction['tx_hash']  # Запоминаем отправленную транзакцию
                            if transaction_info:
                                logger.info(f"Последняя транзакция отправлена в тред {thread_id}")
                        except Exception as e:
                            if int(db.get_setting("API_ERRORS") or 1):
                                logger.error(f"Ошибка отправки последней транзакции: {str(e)}")

            if transaction_info:
                logger.info(f"Проверка завершена. Время: {time.time() - start_time:.2f} сек")

        except Exception as e:
            if int(db.get_setting("API_ERRORS") or 1):
                logger.error(f"Ошибка: {str(e)}")

        await asyncio.sleep(check_interval)

async def start_transaction_monitoring(bot, chat_id):
    logger.info("Запуск мониторинга транзакций")
    await check_token_transactions(bot, chat_id)