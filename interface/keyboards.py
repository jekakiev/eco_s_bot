from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from app_config import db  # Імпортуємо db з app_config
from utils.logger_config import logger, should_log

def get_main_menu():
    keyboard = [
        [
            InlineKeyboardButton(text="📋 Показать кошельки", callback_data="show_wallets"),
            InlineKeyboardButton(text="🪙 Показать токены", callback_data="show_tokens")
        ],
        [
            InlineKeyboardButton(text="ℹ️ Команды", callback_data="show_commands"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="show_settings")
        ],
        [
            InlineKeyboardButton(text="Тест апи (последняя транза)", callback_data="test_api_last_transaction")
        ],
        [
            InlineKeyboardButton(text="Тест апи (по хешу транзы)", callback_data="test_api_by_hash")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_back_button():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Главное меню", callback_data="home")]])

def get_tokens_keyboard(selected_tokens, is_edit=False):
    # Получаем все отслеживаемые токены из базы данных
    tokens = [token[2] for token in db.tracked_tokens.get_all_tracked_tokens()]  # token[2] — token_name
    if should_log("debug"):
        logger.debug(f"Полученные токены из базы: {tokens}")
    keyboard = []
    for i, token in enumerate(tokens):
        callback_data = f"toggle_token_{token}"
        text = f"✅ {token}" if token in selected_tokens else f"❌ {token}"
        if i % 2 == 0 and i + 1 < len(tokens):
            keyboard.append([
                InlineKeyboardButton(text=text, callback_data=callback_data),
                InlineKeyboardButton(text=f"✅ {tokens[i+1]}" if tokens[i+1] in selected_tokens else f"❌ {tokens[i+1]}", callback_data=f"toggle_token_{tokens[i+1]}")
            ])
        elif i % 2 == 0:
            keyboard.append([InlineKeyboardButton(text=text, callback_data=callback_data)])
    if is_edit:
        keyboard.append([InlineKeyboardButton(text="💾 Сохранить", callback_data="save_tokens")])
    else:
        keyboard.append([InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_tokens")])
    keyboard.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="home")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_wallet_control_keyboard(wallet_id):
    keyboard = [
        [
            InlineKeyboardButton(text="✏️ Переименовать", callback_data=f"rename_wallet_{wallet_id}"),
            InlineKeyboardButton(text="🪙 Изменить токены", callback_data=f"edit_tokens_{wallet_id}")
        ],
        [
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_wallet_{wallet_id}"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="home")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_wallets_list():
    wallets = db.wallets.get_all_wallets()
    if not wallets:
        return "📜 Нет добавленных кошельков.", InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="➕ Добавить кошелек", callback_data="add_wallet"), InlineKeyboardButton(text="🏠 Главное меню", callback_data="home")]])
    text = "📜 Список кошельков:\n\n"
    for wallet in wallets:
        text += f"💰 {wallet[2]} ({wallet[1][-4:]}) — /Editw_{wallet[0]}\n"  # wallet[2] — name, wallet[1] — address, wallet[0] — id
    keyboard = [[InlineKeyboardButton(text="➕ Добавить кошелек", callback_data="add_wallet"), InlineKeyboardButton(text="🏠 Главное меню", callback_data="home")]]
    return text, InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_tracked_tokens_list():
    tokens = db.tracked_tokens.get_all_tracked_tokens()
    if not tokens:
        return "🪙 Нет отслеживаемых токенов.", InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="➕ Добавить токен", callback_data="add_token"), InlineKeyboardButton(text="🏠 Главное меню", callback_data="home")]])
    text = "🪙 Список отслеживаемых токенов:\n\n"
    for token in tokens:
        text += f"💎 {token[2]} ({token[1][-4:]}) — /edit_{token[1][-4:]}\n"  # token[2] — token_name, token[1] — contract_address
    keyboard = [[InlineKeyboardButton(text="➕ Добавить токен", callback_data="add_token"), InlineKeyboardButton(text="🏠 Главное меню", callback_data="home")]]
    return text, InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_token_control_keyboard(token_id):
    keyboard = [
        [
            InlineKeyboardButton(text="🧵 Изменить тред", callback_data=f"edit_token_thread_{token_id}"),
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_token_{token_id}")
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="home")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_token_name_confirmation_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Да", callback_data="confirm_token_name"),
            InlineKeyboardButton(text="❌ Нет", callback_data="reject_token_name")
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="home")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_thread_confirmation_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Да", callback_data="thread_exists"),
            InlineKeyboardButton(text="❌ Нет", callback_data="thread_not_exists")
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="home")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_commands_list():
    text = (
        "ℹ️ Список команд:\n\n"
        "*/start* — Запустить бота\n"
        "*/get_thread_id* — Узнать ID текущего треда\n"
        "*/get_last_transaction* — Показать последнюю транзакцию\n"
        "*/Editw_<ID>* — Редактировать кошелек (ID — номер из таблицы кошельков)\n"
        "*/edit_XXXX* — Редактировать токен (XXXX — последние 4 символа адреса контракта)"
    )
    keyboard = [[
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="home")
    ]]
    return text, InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_settings_list(check_interval="150", send_last="❌ВЫКЛ", api_errors="❌ВЫКЛ", transaction_info="✅ВКЛ", interface_info="❌ВЫКЛ", debug="❌ВЫКЛ"):
    text = (
        "⚙️ Настройки бота\n\n"
        "⏱ Интервал проверки — как часто бот проверяет новые транзакции\n"
        "📨 Последняя транзакция — отправка последней транзакции\n"
        "🚨 Ошибки API — логи ошибок внешних API\n"
        "📝 Транзакций — логирование проверки и отправки\n"
        "🖱 Интерфейса — логи действий в меню\n"
        "🔍 Отладка — подробные отладочные сообщения\n"
    )
    keyboard = [
        [
            InlineKeyboardButton(text=f"⏱ Интервал ({check_interval})", callback_data="edit_setting_CHECK_INTERVAL"),
            InlineKeyboardButton(text=f"📨 Последняя транзакция ({send_last})", callback_data="toggle_SEND_LAST_TRANSACTION")
        ],
        [InlineKeyboardButton(text="ЛОГИ", callback_data="noop")],
        [
            InlineKeyboardButton(text=f"🚨 Ошибки API ({api_errors})", callback_data="toggle_API_ERRORS"),
            InlineKeyboardButton(text=f"📝 Транзакции ({transaction_info})", callback_data="toggle_TRANSACTION_INFO")
        ],
        [
            InlineKeyboardButton(text=f"🖱 Интерфейс ({interface_info})", callback_data="toggle_INTERFACE_INFO"),
            InlineKeyboardButton(text=f"🔍 Отладка ({debug})", callback_data="toggle_DEBUG")
        ],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="home")]
    ]
    return text, InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_interval_edit_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="home")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)