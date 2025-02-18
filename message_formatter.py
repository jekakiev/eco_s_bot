def format_swap_message(tx_hash, sender, sender_url, amount_in, token_in, token_in_url, 
                        amount_out, token_out, token_out_url, usd_value):
    """Форматирует сообщение о свапе токенов"""
    message = (
        f"🧾 *Новая транзакция!*
"
        f"👤 [Адрес кошелька]({sender_url}) произвел свап:

"
        f"💱 *{amount_in}* [{token_in}]({token_in_url})
"
        f"🔄 *на* {amount_out} [{token_out}]({token_out_url})

"
        f"💰 *Приблизительная стоимость:* ~${usd_value}
"
        f"🔗 [Детали транзакции](https://arbiscan.io/tx/{tx_hash})"
    )
    return message
