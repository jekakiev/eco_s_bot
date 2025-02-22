from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import Database

db = Database()

# === ГЛАВНОЕ МЕНЮ ===
def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="📜 Список кошельков", callback_data="show_wallets")
    builder.button(text="🪙 Отслеживаемые S токены", callback_data="show_tokens")
    builder.button(text="⚙️ Настройки", callback_data="show_settings")
    builder.button(text="ℹ️ Команды", callback_data="show_commands")
    builder.adjust(1)
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
        text = "📭 У вас пока нет кошельков."
    else:
        text = "Список кошельков:\n"
        for wallet in wallets:
            short_address = wallet['address'][-4:]
            text += f"{wallet['name']} ({short_address}) - /Edit_{short_address}\n"

    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить кошелек", callback_data="add_wallet")
    builder.button(text="⬅️ Назад", callback_data="home")
    builder.adjust(1)
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

# === ВЫБОР ТОКЕНОВ ДЛЯ КОШЕЛЬКА ===
def get_tokens_keyboard(selected_tokens, is_edit=False):
    builder = InlineKeyboardBuilder()

    for token in db.get_all_tracked_tokens():
        token_name = token['token_name']
        is_selected = "✅ " if token_name in selected_tokens else ""
        builder.button(text=f"{is_selected}{token_name}", callback_data=f"toggle_token_{token_name}")

    builder.adjust(2)
    action_text = "💾 Сохранить" if is_edit else "💾 Добавить"
    action_callback = "save_tokens" if is_edit else "confirm_tokens"
    builder.button(text=action_text, callback_data=action_callback)
    builder.button(text="⬅️ В главное меню", callback_data="home")
    builder.adjust(2)
    return builder.as_markup()

# === СПИСОК ОТСЛЕЖИВАЕМЫХ ТОКЕНОВ ===
def get_tracked_tokens_list():
    tokens = db.get_all_tracked_tokens()
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить токен", callback_data="add_token")
    builder.button(text="⬅️ Назад", callback_data="home")
    builder.adjust(1)

    if not tokens:
        text = "📉 Пока мы не отслеживаем ни одного токена."
        return text, builder.as_markup()

    text = "Сейчас мы отслеживаем такие S токены:\n"
    for token in tokens:
        short_address = token['contract_address'][-4:]
        text += f"{token['token_name']} (тред {token['thread_id']}) - /edit_{short_address}\n"
    return text, builder.as_markup()

# === МЕНЮ УПРАВЛЕНИЯ ТОКЕНОМ ===
def get_token_control_keyboard(token_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Изменить тред/ID", callback_data=f"edit_token_{token_id}")
    builder.button(text="🗑 Удалить", callback_data=f"delete_token_{token_id}")
    builder.button(text="⬅️ Назад", callback_data="show_tokens")
    builder.adjust(2)
    return builder.as_markup()

# === ПОДТВЕРЖДЕНИЕ НАЗВАНИЯ ТОКЕНА ===
def get_token_name_confirmation_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да", callback_data="confirm_token_name")
    builder.button(text="❌ Нет", callback_data="reject_token_name")
    builder.adjust(2)
    return builder.as_markup()

# === ПОДТВЕРЖДЕНИЕ СУЩЕСТВОВАНИЯ ТРЕДА ===
def get_thread_confirmation_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да", callback_data="thread_exists")
    builder.button(text="❌ Нет", callback_data="thread_not_exists")
    builder.adjust(2)
    return builder.as_markup()

# === СПИСОК КОМАНД ===
def get_commands_list():
    text = (
        "📋 Доступные команды:\n"
        "`/start` - Запустить бота и показать главное меню\n"
        "`/get_thread_id` - Узнать ID текущего треда\n"
        "`/Edit_XXXX` - Редактировать кошелек (XXXX - последние 4 символа адреса)\n"
        "`/edit_XXXX` - Редактировать токен (XXXX - последние 4 символа контракта)"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data="home")
    builder.adjust(1)
    return text, builder.as_markup()

# === СПИСОК НАСТРОЕК ===
def get_settings_list():
    settings = db.get_all_settings()
    text = (
        "⚙️ Настройки бота:\n"
        "Интервал проверки - Интервал проверки транзакций в секундах (мин. 5)\n"
        "Логи транзакций - Логирование всех транзакций\n"
        "Логи успешных транзакций - Логирование успешных транзакций\n"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text=f"Интервал ({settings['CHECK_INTERVAL']} сек)", callback_data="edit_setting_CHECK_INTERVAL")
    builder.button(text="Настройка логов", callback_data="noop", disabled=True)
    builder.button(text=f"Транзакции ({'Вкл' if int(settings['LOG_TRANSACTIONS']) else 'Выкл'})", callback_data="edit_setting_LOG_TRANSACTIONS")
    builder.button(text=f"Успешные ({'Вкл' if int(settings['LOG_SUCCESSFUL_TRANSACTIONS']) else 'Выкл'})", callback_data="edit_setting_LOG_SUCCESSFUL_TRANSACTIONS")
    builder.button(text="⬅️ Назад", callback_data="home")
    builder.adjust(1, 1, 2, 1)
    return text, builder.as_markup()

# === РЕДАКТИРОВАНИЕ НАСТРОЙКИ CHECK_INTERVAL ===
def get_interval_edit_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data="show_settings")
    builder.button(text="🏠 В главное меню", callback_data="home")
    builder.adjust(2)
    return builder.as_markup()

# === РЕДАКТИРОВАНИЕ НАСТРОЙКИ ЛОГОВ ===
def get_log_edit_keyboard(setting_name):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Вкл", callback_data=f"set_{setting_name}_1")
    builder.button(text="❌ Выкл", callback_data=f"set_{setting_name}_0")
    builder.button(text="⬅️ Назад", callback_data="show_settings")
    builder.button(text="🏠 В главное меню", callback_data="home")
    builder.adjust(2)
    return builder.as_markup()