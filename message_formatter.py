from aiogram.enums import ParseMode

def format_swap_message(tx_hash, sender, sender_url, amount_in, token_in, token_in_url, amount_out, token_out, token_out_url, usd_value):
    try:
        # Функция для форматирования чисел с учётом маленьких значений
        def format_number(value):
            if value == "Неизвестно" or not value:
                return "Неизвестно"
            try:
                num = float(value)
                if num == 0:
                    return "0.00"
                elif 0 < num < 0.0001:  # Если число очень маленькое, используем научную нотацию
                    return f"{num:.6e}"
                elif 0.0001 <= num < 1:  # Для чисел от 0.0001 до 1 показываем до 6 знаков
                    return f"{num:.6f}".rstrip('0').rstrip('.')
                else:  # Для больших чисел используем стандартный формат с 2 знаками
                    return f"{num:,.2f}"
            except (ValueError, TypeError):
                return "Неизвестно"

        # Форматируем суммы, учитывая маленькие значения
        formatted_amount_in = format_number(amount_in)
        formatted_amount_out = format_number(amount_out)
        formatted_usd = format_number(usd_value)

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