from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import Database
from threads_config import TOKEN_CONFIG

db = Database()

# === ГЛАВНОЕ МЕНЮ ===
def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="📜 Список кошельков", callback_data="show_wallets")
    builder.button(text="➕ Добавить кошелек", callback_data="add_wallet")
    builder.adjust(1)  # Одна кнопка в строке
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

    text = "Список кошельков:\n"
    for wallet in wallets:
        short_address = wallet['address'][-4:]
        text += f"{wallet['name']} ({short_address}) - /Edit_{short_address}\n"

    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить кошелек", callback_data="add_wallet")
    builder.button(text="⬅️ Назад", callback_data="home")
    builder.adjust(1)  # Одна кнопка в строке
    return text, builder.as_markup()

# === МЕНЮ УПРАВЛЕНИЯ КОШЕЛЬКОМ ===
def get_wallet_control_keyboard(wallet_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 Удалить", callback_data=f"delete_wallet_{wallet_id}")
    builder.button(text="🔄 Изменить монеты", callback_data=f"edit_tokens_{wallet_id}")
    builder.button(text="✏️ Переименовать", callback_data=f"rename_wallet_{wallet_id}")
    builder.button(text="⬅️ В главное меню", callback_data="home")
    builder.adjust(2)
    return builder.as_markup()

# === ВЫБОР ТОКЕНОВ ===
def get_tokens_keyboard(selected_tokens, is_edit=False):
    builder = InlineKeyboardBuilder()

    for token_name in TOKEN_CONFIG:
        is_selected = "✅ " if token_name in selected_tokens else ""
        builder.button(text=f"{is_selected}{token_name}", callback_data=f"toggle_token_{token_name}")

    builder.adjust(2)

    action_text = "💾 Сохранить" if is_edit else "💾 Добавить"
    action_callback = "save_tokens" if is_edit else "confirm_tokens"
    builder.button(text=action_text, callback_data=action_callback)
    builder.button(text="⬅️ В главное меню", callback_data="home")
    builder.adjust(2)

    return builder.as_markup()