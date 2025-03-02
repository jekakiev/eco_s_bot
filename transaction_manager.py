# /transaction_manager.py
import asyncio
import requests
from aiogram import Bot
from app_config import db
from utils.logger_config import logger, should_log
from config.settings import MORALIS_API_KEY, CHAT_ID, WEBHOOK_URL

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
    """Создание потока для конкретного кошелька через HTTP-запрос."""
    url = "https://api.moralis-streams.com/v2/streams/evm"
    headers = {
        "Authorization": f"Bearer {MORALIS_API_KEY}",
        "Content-Type": "application/json"
    }
    stream_body = {
        "chainIds": ["42161"],  # Arbitrum Mainnet
        "tag": f"wallet_{wallet_address}",
        "description": f"Monitor transactions for {wallet_address}",
        "webhookUrl": WEBHOOK_URL,
        "includeNativeTxs": True,  # Отслеживать нативные транзакции (ETH)
        "includeContractLogs": True,  # Логи смарт-контрактов (токены)
        "topic0": ["Transfer(address,address,uint256)"],  # Трансферы ERC20
        "address": wallet_address  # Адрес кошелька для мониторинга
    }
    
    try:
        if should_log("debug"):
            logger.debug(f"Отправка запроса для создания потока {wallet_address}: {stream_body}")
        
        response = requests.post(url, json=stream_body, headers=headers)
        response.raise_for_status()  # Вызовет исключение, если статус не 2xx
        response_data = response.json()
        
        if should_log("debug"):
            logger.debug(f"Ответ от Moralis Streams API: {response_data}")
        
        if "id" in response_data:
            if should_log("transaction"):
                logger.info(f"Поток успешно создан для {wallet_address}, ID: {response_data['id']}")
        else:
            raise ValueError(f"Неожиданный ответ от Moralis: {response_data}")
            
    except requests.exceptions.RequestException as e:
        if should_log("api_errors"):
            logger.error(f"Ошибка HTTP-запроса для создания потока {wallet_address}: {str(e)}", exc_info=True)
        if should_log("debug"):
            logger.debug(f"Подробности ошибки HTTP-запроса: {e.response.text if e.response else 'Нет ответа'}")
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
        await asyncio.sleep(3600)  # Простая заглушка, чтобы процесс не завершался