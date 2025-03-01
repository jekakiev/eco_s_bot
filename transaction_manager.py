# /transaction_manager.py
import asyncio
from moralis import Moralis, streams  # Импортируем Moralis для инициализации и streams для стримов
from aiogram import Bot
from app_config import db
from utils.logger_config import logger, should_log
from config.settings import MORALIS_API_KEY, CHAT_ID, WEBHOOK_URL
import os

# Инициализация клиента Moralis
Moralis.start({"apiKey": MORALIS_API_KEY})

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
    """Создание потока для конкретного кошелька."""
    try:
        stream_data = {
            "chainIds": ["42161"],  # Arbitrum Mainnet
            "tag": f"wallet_{wallet_address}",
            "description": f"Monitor transactions for {wallet_address}",
            "webhookUrl": WEBHOOK_URL,
            "includeNativeTxs": True,  # Отслеживать нативные транзакции (ETH)
            "includeContractLogs": True,  # Логи смарт-контрактов (токены)
            "topic0": ["Transfer(address,address,uint256)"],  # Трансферы ERC20
            "address": wallet_address  # Адрес кошелька для мониторинга
        }
        if should_log("debug"):
            logger.debug(f"Данные потока для {wallet_address}: {stream_data}")
        
        # Пытаемся использовать streams.create_stream для версии 0.1.49
        streams.create_stream(stream_data)
    except AttributeError as e:
        if should_log("api_errors"):
            logger.error(f"Ошибка: модуль 'moralis.streams' не содержит 'create_stream' для {wallet_address}: {str(e)}", exc_info=True)
        if should_log("debug"):
            logger.debug(f"Попытка использовать альтернативный метод для {wallet_address}", exc_info=True)
        raise  # Пробрасываем, чтобы увидеть в логах
    except Exception as e:
        if should_log("api_errors"):
            logger.error(f"Ошибка создания потока для {wallet_address}: {str(e)}", exc_info=True)
        if should_log("debug"):
            logger.debug(f"Подробности ошибки создания потока для {wallet_address}: {str(e)}", exc_info=True)
        raise

async def start_transaction_monitoring(bot: Bot, chat_id: str):
    """Запуск мониторинга транзакций через Moralis Streams."""
    if should_log("transaction"):
        logger.info("Запуск мониторинга транзакций через Moralis Streams")
    await setup_streams(bot, chat_id)
    # Здесь больше не нужен бесконечный цикл, так как вебхуки работают в реальном времени
    # Для проверки изменений в базе можно добавить периодическую задачу позже
    while True:
        await asyncio.sleep(3600)  # Простая заглушка, чтобы процесс не завершался