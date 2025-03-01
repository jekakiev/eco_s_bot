# /webhook_server.py
from flask import Flask, request, jsonify
from aiogram import Bot
from config.settings import BOT_TOKEN, CHAT_ID, DEFAULT_THREAD_ID
from utils.logger_config import logger, should_log
import asyncio
import threading
import os

app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)
loop = asyncio.get_event_loop()

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
            value = tx.get('value', '0')  # В wei, если нативная транзакция
            
            message = (
                f"📢 Новая транзакция!\n"
                f"Хэш: `{tx_hash}`\n"
                f"От: `{from_address[-4:]}`\n"
                f"К: `{to_address[-4:]}`\n"
                f"Сумма: {value} wei (нативная)\n"
                f"🔗 [Посмотреть](https://arbiscan.io/tx/{tx_hash})"
            )
            
            # Отправка сообщения в Telegram асинхронно
            asyncio.run_coroutine_threadsafe(
                bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown", disable_web_page_preview=True),
                loop
            )
            if should_log("transaction"):
                logger.info(f"Отправлено уведомление о транзакции: {tx_hash}")
        
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