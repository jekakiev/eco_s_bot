from aiogram.enums import ParseMode

def format_number(value):
    if value == "Неизвестно" or not value:
        return "Неизвестно"
    try:
        num = float(value)
        if num == 0:
            return "0.00"
        elif 0 < num < 0.00001:  # Меньше 0.00001 — форматируем с верхним индексом
            exponent = int(-1 * (num.log10() // 1))
            mantissa = num / (10 ** exponent)
            superscript = ''.join(['⁰¹²³⁴⁵⁶⁷⁸⁹'[int(d)] for d in str(exponent)])
            return f"0.0{superscript}1"
        elif 0.00001 <= num < 1:  # От 0.00001 до 1 — показываем как есть
            return f"{num:.6f}".rstrip('0').rstrip('.')
        elif 1 <= num < 1_000_000:  # От 1 до 1 млн — стандартный формат
            return f"{num:,.2f}"
        elif 1_000_000 <= num < 1_000_000_000:  # Миллионы
            return f"{num / 1_000_000:.2f}M"
        elif 1_000_000_000 <= num < 1_000_000_000_000:  # Миллиарды
            return f"{num / 1_000_000_000:.2f}B"
        else:  # Триллионы и больше
            return f"{num / 1_000_000_000_000:.2f}T"
    except (ValueError, TypeError, AttributeError):
        return "Неизвестно"

def format_swap_message(tx_hash, sender, sender_url, amount_in, token_in, token_in_url, amount_out, token_out, token_out_url, usd_value):
    try:
        # Разделяем usd_value на значение и статус, если он есть
        usd_value_str = str(usd_value) if usd_value != "Неизвестно" else "Неизвестно"
        usd_status = ""
        if isinstance(usd_value, str) and "(" in usd_value and ")" in usd_value:
            usd_value_str, usd_status = usd_value.split(" (", 1)
            usd_status = f" ({usd_status.rstrip(')')}"  # Убираем закрывающую скобку и добавляем открывающую для форматирования

        # Форматируем суммы и цену с учётом новых правил
        formatted_amount_in = format_number(amount_in)
        formatted_amount_out = format_number(amount_out)
        formatted_usd = format_number(usd_value_str) + usd_status  # Добавляем статус, если он есть

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