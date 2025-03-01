# /webhook_server.py
from flask import Flask, request, jsonify
from aiogram import Bot
from config.settings import BOT_TOKEN, CHAT_ID, DEFAULT_THREAD_ID
from config.threads_config import DEFAULT_THREAD_ID as DEFAULT_FALLBACK_THREAD_ID
from utils.logger_config import logger, should_log
from app_config import db
import asyncio
import threading
import os
from decimal import Decimal

app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)
loop = asyncio.get_event_loop()

def get_thread_id_for_token(token_name, contract_address):
    """Получение thread_id для токена из базы или дефолтного значения."""
    try:
        # Сначала ищем по имени токена
        tracked_tokens = db.tracked_tokens.get_all_tracked_tokens()
        for token in tracked_tokens:
            if token[2] == token_name or token[1].lower() == contract_address.lower():
                return token[3] if token[3] and token[3].isdigit() else DEFAULT_FALLBACK_THREAD_ID
        return DEFAULT_FALLBACK_THREAD_ID
    except Exception as e:
        if should_log("api_errors"):
            logger.error(f"Ошибка получения thread_id для токена {token_name} или {contract_address}: {str(e)}")
        return DEFAULT_FALLBACK_THREAD_ID

async def convert_to_usd(value, contract_address, decimals=18):
    """Конвертация значения токена в USD через DexScreener API."""
    try:
        if not contract_address or not contract_address.startswith("0x"):
            return Decimal("0")
        base_url = f"https://api.dexscreener.com/latest/dex/tokens/arbitrum/{contract_address}"
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                response.raise_for_status()
                data = await response.json()
                if 'pair' in data and 'baseToken' in data['pair'] and 'priceUsd' in data['pair']['baseToken']:
                    price_usd = Decimal(str(data['pair']['baseToken']['priceUsd']))
                    value_dec = Decimal(str(value)) / Decimal(str(10 ** decimals))
                    return value_dec * price_usd
                if should_log("api_errors"):
                    logger.warning(f"Не удалось получить цену через DexScreener API для {contract_address}")
                return Decimal("0")
    except aiohttp.ClientResponseError as e:
        if should_log("api_errors"):
            if e.status == 404:
                logger.warning(f"Токен {contract_address} не найден в DexScreener API для Arbitrum")
            else:
                logger.warning(f"Ошибка при запросе к DexScreener API для {contract_address}: {str(e)}")
        return Decimal("0")
    except Exception as e:
        if should_log("api_errors"):
            logger.warning(f"Ошибка при запросе к DexScreener API для {contract_address}: {str(e)}")
        return Decimal("0")

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """Обработка вебхуков от Moralis Streams API."""
    try:
        data = request.json
        if should_log("debug"):
            logger.debug(f"Получен вебхук: {data}")
        
        if 'txs' in data and data['txs']:
            tx = data['txs'][0]
            tx_hash = tx.get('hash', 'Неизвестно')
            from_address = tx.get('from', 'Неизвестно')
            to_address = tx.get('to', 'Неизвестно')
            value = tx.get('value', '0')  # В wei для нативных транзакций или в токенах для ERC20
            
            # Определяем, нативная транзакция или токен
            if 'logs' in tx and tx['logs']:
                for log in tx['logs']:
                    if 'topics' in log and log['topics'] and len(log['topics']) > 2:
                        # Это транзакция токена (ERC20 Transfer)
                        contract_address = log['address']
                        token_name = "Неизвестный токен"  # По умолчанию
                        decimals = 18  # По умолчанию
                        
                        # Пытаемся найти токен в базе
                        tracked_tokens = db.tracked_tokens.get_all_tracked_tokens()
                        for token in tracked_tokens:
                            if token[1].lower() == contract_address.lower():
                                token_name = token[2]
                                decimals = int(token[3]) if token[3] and token[3].isdigit() else 18
                                break
                        
                        # Конвертируем значение в USD
                        amount_usd = convert_to_usd(value, contract_address, decimals)
                        
                        # Получаем минимальную сумму для других токенов
                        min_other_token_value = Decimal(db.settings.get_setting("MIN_OTHER_TOKEN_VALUE", "50"))
                        
                        # Определяем thread_id
                        thread_id = get_thread_id_for_token(token_name, contract_address)
                        
                        # Формируем сообщение
                        message = (
                            f"📢 Новая транзакция токена!\n"
                            f"Токен: `{token_name}`\n"
                            f"Хэш: `{tx_hash}`\n"
                            f"От: `{from_address[-4:]}`\n"
                            f"К: `{to_address[-4:]}`\n"
                            f"Сумма: {Decimal(value) / Decimal(10 ** decimals):.6f} {token_name}\n"
                            f"Сумма (USD): ${amount_usd:.2f}\n"
                            f"🔗 [Посмотреть](https://arbiscan.io/tx/{tx_hash})"
                        )
                        
                        # Отправляем, если сумма превышает минимальную (для неподдерживаемых токенов)
                        if token_name == "Неизвестный токен" and amount_usd < min_other_token_value:
                            if should_log("transaction"):
                                logger.info(f"Транзакция токена {contract_address} проигнорирована: сумма ${amount_usd:.2f} меньше минимальной ${min_other_token_value}")
                            return jsonify({"status": "success"}), 200
                        
                        # Отправка сообщения в Telegram асинхронно
                        asyncio.run_coroutine_threadsafe(
                            bot.send_message(
                                chat_id=CHAT_ID,
                                text=message,
                                parse_mode="Markdown",
                                disable_web_page_preview=True,
                                message_thread_id=thread_id if thread_id != DEFAULT_FALLBACK_THREAD_ID else None
                            ),
                            loop
                        )
                        if should_log("transaction"):
                            logger.info(f"Отправлено уведомление о транзакции токена {token_name}: {tx_hash} в тред {thread_id}")
                        return jsonify({"status": "success"}), 200
            else:
                # Нативная транзакция (ETH)
                amount_usd = await convert_to_usd(value, "0x0000000000000000000000000000000000000000", 18)  # ETH на Arbitrum
                thread_id = DEFAULT_FALLBACK_THREAD_ID  # По умолчанию для нативных транзакций
                
                message = (
                    f"📢 Новая транзакция!\n"
                    f"Хэш: `{tx_hash}`\n"
                    f"От: `{from_address[-4:]}`\n"
                    f"К: `{to_address[-4:]}`\n"
                    f"Сумма: {Decimal(value) / Decimal(10 ** 18):.6f} ETH\n"
                    f"Сумма (USD): ${amount_usd:.2f}\n"
                    f"🔗 [Посмотреть](https://arbiscan.io/tx/{tx_hash})"
                )
                
                # Отправка сообщения в Telegram асинхронно
                asyncio.run_coroutine_threadsafe(
                    bot.send_message(
                        chat_id=CHAT_ID,
                        text=message,
                        parse_mode="Markdown",
                        disable_web_page_preview=True,
                        message_thread_id=thread_id if thread_id != DEFAULT_FALLBACK_THREAD_ID else None
                    ),
                    loop
                )
                if should_log("transaction"):
                    logger.info(f"Отправлено уведомление о нативной транзакции: {tx_hash} в тред {thread_id}")
        
        return jsonify({"status": "success"}), 200
    except Exception as e:
        if should_log("api_errors"):
            logger.error(f"Ошибка обработки вебхука: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

def run_flask():
    """Запуск Flask сервера в отдельном потоке с динамическим портом."""
    port = int(os.getenv("PORT", 8080))  # Используем PORT из окружения или 8080 по умолчанию
    logger.info(f"Flask сервер запускается на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == "__main__":
    # Запуск Flask в отдельном потоке
    threading.Thread(target=run_flask, daemon=True).start()
    logger.info("Flask сервер запущен для обработки вебхуков")