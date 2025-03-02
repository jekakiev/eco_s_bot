# /transaction_manager.py
import asyncio
from moralis import streams
import moralis  # Для проверки версии
from aiogram import Bot
from app_config import db
from utils.logger_config import logger, should_log
from config.settings import MORALIS_API_KEY, CHAT_ID, WEBHOOK_URL

# Логируем версию moralis
logger.info(f"Используемая версия moralis: {moralis.__version__}")

async def setup_streams(bot: Bot, chat_id: str):
    """Настройка потоков Moralis для всех кошельков из базы."""
    try:
        db.reconnect()
        wallets = db.wallets.get_all_wallets()
        if not wallets:
            if should_log("debug"):
                logger.debug("Пустой список кошельков в базе данных")
            logger.warning("Нет кошельков в базе для настройки потоков")
            return
        
        wallet_addresses = [wallet[1] for wallet in wallets]
        if should_log("debug"):
            logger.debug(f"Получены Addresses кошельков из базы: {wallet_addresses}")
        
        # Шаг 1: Создаём стрим
        stream_body = {
            "webhookUrl": WEBHOOK_URL,
            "description": "Monitor transactions for bot wallets",
            "tag": "bot_wallets_stream",
            "chainIds": ["0x1a4"],  # Arbitrum Mainnet в hex (42161)
            "includeNativeTxs": True,
            "includeContractLogs": True,
            "topic0": ["Transfer(address,address,uint256)"]
        }
        
        if should_log("debug"):
            logger.debug(f"Создание стрима: {stream_body}")
        
        result = streams.evm_streams.create_stream(api_key=MORALIS_API_KEY, body=stream_body)
        
        if should_log("debug"):
            logger.debug(f"Ответ от Moralis Streams при создании: {result}")
        
        stream_id = result.get("id")
        if not stream_id:
            raise ValueError(f"Не удалось создать стрим, нет ID: {result}")
        
        if should_log("transaction"):
            logger.info(f"Стрим успешно создан, ID: {stream_id}")
        
        # Шаг 2: Добавляем адреса к стриму
        add_body = {
            "address": wallet_addresses  # Список всех адресов
        }
        params = {"id": stream_id}
        
        if should_log("debug"):
            logger.debug(f"Добавление адресов к стриму {stream_id}: {add_body}")
        
        add_result = streams.evm_streams.add_address_to_stream(api_key=MORALIS_API_KEY, body=add_body, params=params)
        
        if should_log("debug"):
            logger.debug(f"Ответ от Moralis Streams при добавлении адресов: {add_result}")
        
        if should_log("transaction"):
            logger.info(f"Адреса успешно добавлены к стриму {stream_id}: {wallet_addresses}")
        
        logger.info("Все потоки Moralis настроены")
        
    except Exception as e:
        if should_log("api_errors"):
            logger.error(f"Ошибка при настройке потоков: {str(e)}", exc_info=True)
        if should_log("debug"):
            logger.debug(f"Подробности ошибки настройки потоков: {str(e)}", exc_info=True)
        raise

async def start_transaction_monitoring(bot: Bot, chat_id: str):
    """Запуск мониторинга транзакций через Moralis Streams."""
    if should_log("transaction"):
        logger.info("Запуск мониторинга транзакций через Moralis Streams")
    await setup_streams(bot, chat_id)
    while True:
        await asyncio.sleep(3600)