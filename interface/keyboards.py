from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import Database
from threads_config import TOKEN_CONFIG

db = Database()

# === ГЛАВНЕ МЕНЮ ===
def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="📜 Показати гаманці", callback_data="show_wallets")
    builder.button(text="➕ Додати гаманець", callback_data="add_wallet")
    return builder.as_markup()

# === КНОПКА НАЗАД ===
def get_back_button():
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ У головне меню", callback_data="home")
    return builder.as_markup()

# === СПИСОК ГАМАНЦІВ ===
def get_wallets_list():
    wallets = db.get_all_wallets()
    if not wallets:
        return "📭 У вас поки немає гаманців."

    text = "📜 *Ваші гаманці:*\n\n"
    for wallet in wallets:
        short_address = wallet['address'][-4:]
        text += f"🔹 {wallet['name']} ({short_address}) — /Edit_{short_address}\n"

    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data="home")
    builder.adjust(1)  # Розташовуємо кнопку в один стовпець

    return text, builder.as_markup()

# === МЕНЮ УПРАВЛІННЯ ГАМАНЦЕМ ===
def get_wallet_control_keyboard(wallet_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 Видалити", callback_data=f"delete_wallet_{wallet_id}")
    builder.button(text="🔄 Змінити монети", callback_data=f"edit_tokens_{wallet_id}")
    builder.button(text="✏️ Перейменувати", callback_data=f"rename_wallet_{wallet_id}")
    builder.button(text="⬅️ У головне меню", callback_data="home")
    builder.adjust(2)  # Розташовуємо кнопки по 2 в ряд
    return builder.as_markup()

# === ВИБІР ТОКЕНІВ (2 КНОПКИ В РЯД) ===
def get_tokens_keyboard(selected_tokens):
    builder = InlineKeyboardBuilder()

    for token_name in TOKEN_CONFIG:
        is_selected = "✅ " if token_name in selected_tokens else ""
        builder.button(text=f"{is_selected}{token_name}", callback_data=f"toggle_token_{token_name}")

    # Розташовуємо кнопки по 2 в ряд
    builder.adjust(2)

    # Внизу робимо кнопки "Додати" і "Назад" в один ряд
    builder.button(text="✅ Додати", callback_data="confirm_tokens")
    builder.button(text="⬅️ У головне меню", callback_data="home")
    builder.adjust(2)  # Щоб вони також були в ряд

    return builder.as_markup()