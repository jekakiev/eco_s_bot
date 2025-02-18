def format_swap_message(tx_hash, sender, sender_url, amount_in, token_in, token_in_url, 
                        amount_out, token_out, token_out_url, usd_value):
    """Форматирует сообщение о свапе токенов"""
    message = (
        f"🧾 *Новая транзакция!*\n"
        f"👤 [{sender}]({sender_url}) совершил свап:\n\n"
        f"💱 *{amount_in}* [{token_in}]({token_in_url})\n"
        f"🔄 *на* {amount_out} [{token_out}]({token_out_url})\n\n"
        f"💰 *Приблизительная стоимость:* ~${usd_value}\n"
        f"🔗 [Детали транзакции](https://arbiscan.io/tx/{tx_hash})"
    )
    return message
