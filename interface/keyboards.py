from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import Database
from threads_config import TOKEN_CONFIG

db = Database()

# === ГЛАВНОЕ МЕНЮ ===
def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="📜 Показать кошельки", callback_data="show_wallets")
    builder.button(text="➕ Добавить кошелек", callback_data="add_wallet")
    return builder.as_markup()

# === КНОПКА НАЗАД ===
def get_back_button():
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ В главное меню", callback_data="home")
    return builder.as_markup()

# === СПИСОК КОШЕЛЬКОВ ===
def get_wallets_list():
    wallets = db.get_all_wallets()
    if not wallets:
        return "📭 У вас пока нет кошельков."

    text = "📜 *Ваши кошельки:*\n\n"
    for wallet in wallets:
        short_address = wallet['address'][-4:]
        text += f"🔹 {wallet['name']} ({short_address})\n"
    text += "\nℹ️ Используйте команду `/Edit_КОРОТКИЙ_АДРЕС` для редактирования."

    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data="home")
    builder.adjust(1)  # Располагаем кнопку в один столбец

    return text, builder.as_markup()

# === МЕНЮ УПРАВЛЕНИЯ КОШЕЛЬКОМ ===
def get_wallet_control_keyboard(wallet_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 Удалить", callback_data=f"delete_wallet_{wallet_id}")
    builder.button(text="🔄 Изменить монеты", callback_data=f"edit_tokens_{wallet_id}")
    builder.button(text="✏️ Переименовать", callback_data=f"rename_wallet_{wallet_id}")
    builder.button(text="⬅️ В главное меню", callback_data="home")
    builder.adjust(2)  # Располагаем кнопки по 2 в ряд
    return builder.as_markup()

# === ВЫБОР ТОКЕНОВ (2 КНОПКИ В РЯД) ===
def get_tokens_keyboard(selected_tokens):
    builder = InlineKeyboardBuilder()

    for token_name in TOKEN_CONFIG:
        is_selected = "✅ " if token_name in selected_tokens else ""
        builder.button(text=f"{is_selected}{token_name}", callback_data=f"toggle_token_{token_name}")

    # Располагаем кнопки по 2 в ряд
    builder.adjust(2)

    # Внизу делаем кнопки "Добавить" и "Назад" в один ряд
    builder.button(text="✅ Добавить", callback_data="confirm_tokens")
    builder.button(text="⬅️ В главное меню", callback_data="home")
    builder.adjust(2)  # Чтобы они тоже были в ряд

    return builder.as_markup()