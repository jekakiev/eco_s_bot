from aiogram import types, Dispatcher
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from database import Database
from threads_config import TOKEN_CONFIG

db = Database()

# Главное меню
def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="📜 Показать кошельки", callback_data="show_wallets")
    builder.button(text="➕ Добавить кошелек", callback_data="add_wallet")
    return builder.as_markup()

# Получить список кошельков (гиперссылками)
def get_wallets_list():
    wallets = db.get_all_wallets()
    if not wallets:
        return "📭 У вас пока нет кошельков."

    text = "📜 Ваши кошельки:\n"
    for wallet in wallets:
        text += f"🔹 [{wallet['name'] or wallet['address'][:6] + '...'}](https://arbiscan.io/address/{wallet['address']})\n"

    return text

# Клавиатура для управления кошельком
def get_wallet_control_keyboard(wallet_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 Удалить", callback_data=f"delete_wallet_{wallet_id}")
    builder.button(text="🔄 Изменить монеты", callback_data=f"edit_tokens_{wallet_id}")
    builder.button(text="✏️ Переименовать", callback_data=f"rename_wallet_{wallet_id}")
    builder.button(text="⬅️ В главное меню", callback_data="home")
    return builder.as_markup()

# Выбор токенов (2 кнопки в ряд)
def get_tokens_keyboard(selected_tokens):
    builder = InlineKeyboardBuilder()
    
    for token_name, config in TOKEN_CONFIG.items():
        is_selected = "✅ " if token_name in selected_tokens else ""
        builder.button(text=f"{is_selected}{token_name}", callback_data=f"toggle_token_{token_name}")

    builder.adjust(2)  # Две кнопки в ряд
    builder.button(text="✅ Добавить", callback_data="confirm_tokens")
    builder.button(text="⬅️ В главное меню", callback_data="home")
    
    return builder.as_markup()

# Обработчик команды /wallets
async def wallets_command(message: types.Message):
    await message.answer(get_wallets_list(), parse_mode="Markdown", disable_web_page_preview=True)

# Обработчик кнопки "Показать кошельки"
async def show_wallets(callback: types.CallbackQuery):
    await callback.message.edit_text(get_wallets_list(), parse_mode="Markdown", disable_web_page_preview=True)

# Обработчик кнопки "Добавить кошелек"
async def add_wallet_start(callback: types.CallbackQuery, state: Dispatcher):
    await state.set_state("add_wallet_address")
    await callback.message.edit_text("📝 Введите адрес кошелька:")

# Ввод адреса
async def process_wallet_address(message: types.Message, state: Dispatcher):
    await state.update_data(wallet_address=message.text)
    await state.set_state("add_wallet_name")
    await message.answer("✏️ Введите название кошелька:")

# Ввод имени
async def process_wallet_name(message: types.Message, state: Dispatcher):
    await state.update_data(wallet_name=message.text)
    await state.set_state("add_wallet_tokens")
    await message.answer("🪙 Выберите монеты для отслеживания:", reply_markup=get_tokens_keyboard([]))

# Выбор токенов
async def toggle_token(callback: types.CallbackQuery, state: Dispatcher):
    token = callback.data.split("_")[1]
    data = await state.get_data()
    selected_tokens = data.get("selected_tokens", [])

    if token in selected_tokens:
        selected_tokens.remove(token)
    else:
        selected_tokens.append(token)

    await state.update_data(selected_tokens=selected_tokens)
    await callback.message.edit_text("🪙 Выберите монеты для отслеживания:", reply_markup=get_tokens_keyboard(selected_tokens))

# Подтверждение выбора токенов
async def confirm_tokens(callback: types.CallbackQuery, state: Dispatcher):
    data = await state.get_data()
    wallet_address = data.get("wallet_address")
    wallet_name = data.get("wallet_name")
    selected_tokens = data.get("selected_tokens", [])

    if not selected_tokens:
        await callback.answer("⚠️ Вы не выбрали ни одного токена!", show_alert=True)
        return

    db.add_wallet(wallet_address, wallet_name, ",".join(selected_tokens))
    await state.clear()
    await callback.message.edit_text("✅ Кошелек добавлен!", reply_markup=get_main_menu())

# Удаление кошелька
async def delete_wallet(callback: types.CallbackQuery):
    wallet_id = callback.data.split("_")[2]
    db.remove_wallet(wallet_id)
    await callback.message.edit_text("🗑 Кошелек удален!", reply_markup=get_main_menu())

# Обработчик "В главное меню"
async def go_home(callback: types.CallbackQuery):
    await callback.message.edit_text("🏠 Главное меню:", reply_markup=get_main_menu())

# Регистрация обработчиков
def register_handlers(dp: Dispatcher):
    dp.message.register(wallets_command, Command("wallets"))
    dp.callback_query.register(show_wallets, lambda c: c.data == "show_wallets")
    dp.callback_query.register(add_wallet_start, lambda c: c.data == "add_wallet")
    dp.message.register(process_wallet_address, lambda message, state: state.get_state() == "add_wallet_address")
    dp.message.register(process_wallet_name, lambda message, state: state.get_state() == "add_wallet_name")
    dp.callback_query.register(toggle_token, lambda c: c.data.startswith("toggle_token_"))
    dp.callback_query.register(confirm_tokens, lambda c: c.data == "confirm_tokens")
    dp.callback_query.register(delete_wallet, lambda c: c.data.startswith("delete_wallet_"))
    dp.callback_query.register(go_home, lambda c: c.data == "home")
