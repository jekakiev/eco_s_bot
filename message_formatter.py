def format_swap_message(tx_hash, sender, sender_url, amount_in, token_in, token_in_url, 
                        amount_out, token_out, token_out_url, usd_value):
    """
    Форматує повідомлення про свап токенів.
    
    Аргументи:
        tx_hash (str): Хеш транзакції.
        sender (str): Адреса відправника.
        sender_url (str): URL профілю відправника.
        amount_in (float): Кількість вхідного токена.
        token_in (str): Назва вхідного токена.
        token_in_url (str): URL токена, який обмінюється.
        amount_out (float): Кількість вихідного токена.
        token_out (str): Назва вихідного токена.
        token_out_url (str): URL токена, який отримано.
        usd_value (str | float): Приблизна вартість свапу у доларах.

    Повертає:
        tuple: (відформатоване повідомлення, "Markdown")
    """

    message = (
        f"🧾 *Нова транзакція!*\n"
        f"👤 [{sender}]({sender_url}) здійснив свап:\n\n"
        f"💱 *{amount_in:.4f}* [{token_in}]({token_in_url})\n"
        f"🔄 *на* {amount_out:.4f} [{token_out}]({token_out_url})\n\n"
        f"💰 *Приблизна вартість:* ~${usd_value}\n"
        f"🔗 [Деталі транзакції](https://arbiscan.io/tx/{tx_hash})"
    )

    return message, "Markdown"  # Формат для Telegram API
