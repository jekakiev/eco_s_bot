def format_swap_message(tx_hash, sender, sender_url, amount_in, token_in, token_in_url, amount_out, token_out, token_out_url, usd_value):
    """
    Форматирует сообщение о своп-транзакции для отправки в Telegram.
    """
    try:
        message = (
            f"🔔 Новая транзакция!\n\n"
            f"📤 Отправитель: [{sender}]({sender_url})\n"
            f"📥 Токен IN: [{token_in}]({token_in_url}) — {amount_in}\n"
            f"📤 Токен OUT: [{token_out}]({token_out_url}) — {amount_out}\n"
            f"💰 USD: {usd_value}\n"
            f"🔗 [Посмотреть транзакцию](https://arbiscan.io/tx/{tx_hash})"
        )
        return message, "Markdown"
    except Exception as e:
        return f"Ошибка форматирования сообщения: {str(e)}", None