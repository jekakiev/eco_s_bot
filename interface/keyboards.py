from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database import Database

db = Database()

def get_main_menu():
    keyboard = [
        [
            InlineKeyboardButton(text="📋 Показать кошельки", callback_data="show_wallets"),
            InlineKeyboardButton(text="🪙 Показать токены", callback_data="show_tokens")
        ],
        [
            InlineKeyboardButton(text="ℹ️ Команды", callback_data="show_commands"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="show_settings")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_back_button():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Главное меню", callback_data="home")]])

def get_tokens_keyboard(selected_tokens, is_edit=False):
    tokens = [
        "HITCOIN",
        "S",
        "ROSTIKSON 2.0",
        "GRIMASS"
    ]
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
    wallets = db.get_all_wallets()
    if not wallets:
        return "📜 Нет добавленных кошельков.", get_main_menu()
    text = "📜 Список кошельков:\n\n"
    for wallet in wallets:
        text += f"💰 {wallet['name']} — {wallet['address'][-4:]}\n"
    keyboard = [
        [
            InlineKeyboardButton(text="➕ Добавить кошелек", callback_data="add_wallet"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="home")
        ]
    ]
    return text, InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_tracked_tokens_list():
    tokens = db.get_all_tracked_tokens()
    if not tokens:
        return "🪙 Нет отслеживаемых токенов.", get_main_menu()
    text = "🪙 Список отслеживаемых токенов:\n\n"
    for token in tokens:
        text += f"💎 {token['token_name']} — {token['contract_address'][-4:]} (Тред: {token['thread_id']})\n"
    keyboard = [
        [
            InlineKeyboardButton(text="➕ Добавить токен", callback_data="add_token"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="home")
        ]
    ]
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
        "*/Edit_XXXX* — Редактировать кошелек (XXXX — последние 4 символа адреса)\n"
        "*/edit_XXXX* — Редактировать токен (XXXX — последние 4 символа адреса контракта)"
    )
    keyboard = [[
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="home")
    ]]
    return text, InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_settings_list():
    # Всегда получаем свежие данные из базы
    settings = db.get_all_settings()
    check_interval = settings.get("CHECK_INTERVAL", "10")
    send_last = "✅" if settings.get("SEND_LAST_TRANSACTION", "0") == "1" else "❌"
    api_errors = "✅" if settings.get("API_ERRORS", "1") == "1" else "❌"
    transaction_info = "✅" if settings.get("TRANSACTION_INFO", "0") == "1" else "❌"
    interface_info = "✅" if settings.get("INTERFACE_INFO", "0") == "1" else "❌"
    debug = "✅" if settings.get("DEBUG", "0") == "1" else "❌"
    
    text = (
        "⚙️ Настройки бота:\n\n"
        "⏱ Интервал проверки — интервал между проверками транзакций (в секундах).\n"
        "📨 Последняя транзакция — отправка последней транзакции каждые CHECK_INTERVAL секунд.\n"
        "🚨 Ошибки API — логи ошибок внешних API (DexScreener, Arbiscan).\n"
        "📝 Логи транзакций — информация о проверке и отправке транзакций.\n"
        "🖱 Логи интерфейса — действия в меню и командах.\n"
        "🔍 Отладка — подробные отладочные сообщения."
    )
    keyboard = [
        [
            InlineKeyboardButton(text=f"⏱ Интервал проверки ({check_interval} сек)", callback_data="edit_setting_CHECK_INTERVAL"),
            InlineKeyboardButton(text=f"📨 Последняя транзакция ({send_last})", callback_data="toggle_SEND_LAST_TRANSACTION")
        ],
        [
            InlineKeyboardButton(text=f"🚨 Ошибки API ({api_errors})", callback_data="toggle_API_ERRORS"),
            InlineKeyboardButton(text=f"📝 Логи транзакций ({transaction_info})", callback_data="toggle_TRANSACTION_INFO")
        ],
        [
            InlineKeyboardButton(text=f"🖱 Логи интерфейса ({interface_info})", callback_data="toggle_INTERFACE_INFO"),
            InlineKeyboardButton(text=f"🔍 Отладка ({debug})", callback_data="toggle_DEBUG")
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="home")
        ]
    ]
    return text, InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_interval_edit_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="home")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)