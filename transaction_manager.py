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
        
        if should_log("debug"):
            logger.debug(f"Получены кошельки из базы: {wallets}")
        
        for wallet in wallets:
            wallet_address = wallet[1]
            if should_log("debug"):
                logger.debug(f"Настройка потока для кошелька: {wallet_address}")
            await create_stream(wallet_address)
            if should_log("transaction"):
                logger.info(f"Поток создан для кошелька: {wallet_address}")
        
        logger.info("Все потоки Moralis настроены")
    except Exception as e:
        if should_log("api_errors"):
            logger.error(f"Ошибка при настройке потоков: {str(e)}", exc_info=True)
        if should_log("debug"):
            logger.debug(f"Подробности ошибки настройки потоков: {str(e)}", exc_info=True)

async def create_stream(wallet_address):
    """Создание потока для конкретного кошелька согласно инструкции Moralis."""
    stream_body = {
        "webhookUrl": WEBHOOK_URL,
        "description": f"Monitor transactions for {wallet_address}",
        "tag": f"wallet_{wallet_address}",
        "chainIds": ["0x1a4"],  # Arbitrum Mainnet в hex (42161)
        "includeNativeTxs": True,
        "includeContractLogs": True,
        "topic0": ["Transfer(address,address,uint256)"],
        "address": wallet_address
    }
    
    try:
        if should_log("debug"):
            logger.debug(f"Создание потока для {wallet_address}: {stream_body}")
        
        result = streams.evm_streams.create_stream(api_key=MORALIS_API_KEY, body=stream_body)
        
        if should_log("debug"):
            logger.debug(f"Ответ от Moralis Streams: {result}")
        
        if "id" in result:
            if should_log("transaction"):
                logger.info(f"Поток успешно создан для {wallet_address}, ID: {result['id']}")
        else:
            raise ValueError(f"Неожиданный ответ от Moralis: {result}")
            
    except AttributeError as e:
        if should_log("api_errors"):
            logger.error(f"Ошибка: метод create_stream недоступен в moralis.streams: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        if should_log("api_errors"):
            logger.error(f"Ошибка создания потока для {wallet_address}: {str(e)}", exc_info=True)
        if should_log("debug"):
            logger.debug(f"Подробности ошибки создания потока: {str(e)}")
        raise

async def start_transaction_monitoring(bot: Bot, chat_id: str):
    """Запуск мониторинга транзакций через Moralis Streams."""
    if should_log("transaction"):
        logger.info("Запуск мониторинга транзакций через Moralis Streams")
    await setup_streams(bot, chat_id)
    while True:
        await asyncio.sleep(3600)