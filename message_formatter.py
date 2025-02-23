from aiogram.enums import ParseMode

def format_swap_message(tx_hash, sender, sender_url, amount_in, token_in, token_in_url, amount_out, token_out, token_out_url, usd_value):
    try:
        # Форматируем суммы, убирая лишние нули и приводя к читаемому виду
        formatted_amount_in = f"{float(amount_in):,.2f}" if amount_in and amount_in != "Неизвестно" else "Неизвестно"
        formatted_amount_out = f"{float(amount_out):,.2f}" if amount_out and amount_out != "Неизвестно" else "Неизвестно"
        formatted_usd = f"{float(usd_value):,.2f}" if usd_value and usd_value != "Неизвестно" else "Неизвестно"

        # Формируем сообщение
        message = (
            f"📢 Новая транзакция!\n\n"
            f"👤 Отправитель: [{sender}]({sender_url})\n"
            f"📥 Токен IN: [{token_in}]({token_in_url}) — {formatted_amount_in}\n"
            f"📤 Токен OUT: [{token_out}]({token_out_url}) — {formatted_amount_out}\n"
            f"💰 USD: ${formatted_usd}\n"
            f"🔗 [Посмотреть транзакцию](https://arbiscan.io/tx/{tx_hash})"
        )
        return message, ParseMode.MARKDOWN
    except Exception as e:
        return f"Ошибка форматирования сообщения: {str(e)}", None