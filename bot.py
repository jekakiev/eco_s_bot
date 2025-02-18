import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import BOT_TOKEN
from arbiscan import get_token_transactions
from message_formatter import format_swap_message
from wallets_config import WATCHED_WALLETS

# Ініціалізуємо бота та диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Налаштування
CHECK_INTERVAL = 10  # Перевірка кожні 10 секунд
THREAD_ID = 7  # ID треду
CHAT_ID = -1002458140371  # ID чату

# Словник останніх хешів транзакцій
last_tx_hash = {}

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("✅ Бот запущено!")

@dp.message(Command("get_chat_id"))
async def get_chat_id(message: types.Message):
    thread_id = message.message_thread_id
    chat_info = f"🆔 Chat ID: `{message.chat.id}`"

    if thread_id:
        chat_info += f"\n🧵 Thread ID: `{thread_id}`"

    await message.answer(chat_info, parse_mode="Markdown")

async def check_token_transactions():
    """Функція перевірки нових транзакцій"""
    global last_tx_hash

    while True:
        for wallet_address, wallet_name in WATCHED_WALLETS.items():
            transactions = get_token_transactions(wallet_address)

            if transactions:
                for tx_hash, tx_list in transactions.items():
                    if last_tx_hash.get(wallet_address) == tx_hash:
                        continue  # Пропускаємо, якщо вже оброблено

                    last_tx_hash[wallet_address] = tx_hash

                    # Визначаємо входи та виходи токенів
                    sender = tx_list[0]["from"]
                    recipient = tx_list[0]["to"]

                    amount_in, token_in, token_in_url = "?", "?", "#"
                    amount_out, token_out, token_out_url = "?", "?", "#"

                    for tx in tx_list:
                        if tx["from"].lower() == wallet_address.lower():
                            amount_in = float(tx["value"]) / (10 ** int(tx["tokenDecimal"]))
                            token_in = tx["tokenName"]
                            token_in_url = f"https://arbiscan.io/token/{tx['contractAddress']}"
                        if tx["to"].lower() == wallet_address.lower():
                            amount_out = float(tx["value"]) / (10 ** int(tx["tokenDecimal"]))
                            token_out = tx["tokenName"]
                            token_out_url = f"https://arbiscan.io/token/{tx['contractAddress']}"

                    # Генерація повідомлення
                    text, parse_mode = format_swap_message(
                        tx_hash=tx_hash,
                        sender=wallet_name,
                        sender_url=f"https://arbiscan.io/address/{wallet_address}",
                        amount_in=amount_in,
                        token_in=token_in,
                        token_in_url=token_in_url,
                        amount_out=amount_out,
                        token_out=token_out,
                        token_out_url=token_out_url,
                        usd_value="?"
                    )

                    # Відправка повідомлення у чат
                    await bot.send_message(
                        chat_id=CHAT_ID,
                        message_thread_id=THREAD_ID,
                        text=text,
                        parse_mode=parse_mode,
                        disable_web_page_preview=True
                    )

        await asyncio.sleep(CHECK_INTERVAL)

async def main():
    asyncio.create_task(check_token_transactions())  
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
