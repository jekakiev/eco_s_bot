import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command, StateFilter
from database import Database
from threads_config import TOKEN_CONFIG

db = Database()

# === СТАНЫ ДЛЯ FSM ===
class AddWalletState(StatesGroup):
    address = State()
    name = State()
    tokens = State()

# === ГЛАВНОЕ МЕНЮ ===
def get_main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="💼 Управление кошельками", callback_data="wallets_menu")
    return builder.as_markup()

# === КНОПКИ СПИСКА КОШЕЛЬКОВ ===
def get_wallets_keyboard():
    builder = InlineKeyboardBuilder()
    wallets = db.get_all_wallets()
    
    for wallet in wallets:
        builder.button(text=wallet["name"], callback_data=f"wallet_{wallet['id']}")  # wallet_id
    builder.button(text="➕ Добавить кошелек", callback_data="add_wallet")
    builder.button(text="⬅️ Вернуться в главное меню", callback_data="home")
    
    return builder.as_markup()

# === МЕНЮ УПРАВЛЕНИЯ КОШЕЛЬКОМ ===
def get_wallet_control_keyboard(wallet_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 Удалить", callback_data=f"delete_wallet_{wallet_id}")
    builder.button(text="🔄 Изменить токены", callback_data=f"edit_tokens_{wallet_id}")
    builder.button(text="✏️ Переименовать", callback_data=f"rename_wallet_{wallet_id}")
    builder.button(text="⬅️ Назад к списку кошельков", callback_data="wallets_menu")
    
    return builder.as_markup()

# === КНОПКИ ВЫБОРА ТОКЕНОВ ===
def get_tokens_keyboard(selected_tokens):
    builder = InlineKeyboardBuilder()
    
    for token_name, config in TOKEN_CONFIG.items():
        is_selected = "✅ " if token_name in selected_tokens else ""
        builder.button(text=f"{is_selected}{token_name}", callback_data=f"toggle_token_{token_name}")

    builder.button(text="✅ Подтвердить", callback_data="confirm_tokens")
    builder.button(text="⬅️ Вернуться в главное меню", callback_data="home")
    
    return builder.as_markup()

# === ГЛАВНОЕ МЕНЮ ===
async def start_command(message: types.Message):
    await message.answer("🏠 Главное меню:", reply_markup=get_main_keyboard())

# === ОТКРЫТЬ МЕНЮ КОШЕЛЬКОВ ===
async def wallets_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("📜 Ваши кошельки:", reply_markup=get_wallets_keyboard())

# === ОТКРЫТЬ МЕНЮ КОНКРЕТНОГО КОШЕЛЬКА ===
async def wallet_callback(callback: types.CallbackQuery):
    wallet_id = callback.data.split("_")[1]
    await callback.message.edit_text(f"⚙️ Управление кошельком:", reply_markup=get_wallet_control_keyboard(wallet_id))

# === НАЧАЛО ДОБАВЛЕНИЯ КОШЕЛЬКА ===
async def add_wallet_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AddWalletState.address)
    await callback.message.edit_text("📝 Введите адрес кошелька:")

# === ВВОД АДРЕСА КОШЕЛЬКА ===
async def process_wallet_address(message: types.Message, state: FSMContext):
    await state.update_data(wallet_address=message.text)
    await state.set_state(AddWalletState.name)
    await message.answer("✏️ Введите имя кошелька:")

# === ВВОД ИМЕНИ КОШЕЛЬКА ===
async def process_wallet_name(message: types.Message, state: FSMContext):
    await state.update_data(wallet_name=message.text)
    await state.set_state(AddWalletState.tokens)
    await message.answer("🪙 Выберите токены для отслеживания:", reply_markup=get_tokens_keyboard([]))

# === ВЫБОР ТОКЕНОВ ===
async def toggle_token(callback: types.CallbackQuery, state: FSMContext):
    token = callback.data.split("_")[1]
    data = await state.get_data()
    selected_tokens = data.get("selected_tokens", [])

    if token in selected_tokens:
        selected_tokens.remove(token)
    else:
        selected_tokens.append(token)

    await state.update_data(selected_tokens=selected_tokens)
    await callback.message.edit_text("🪙 Выберите токены для отслеживания:", reply_markup=get_tokens_keyboard(selected_tokens))

# === ПОДТВЕРЖДЕНИЕ ВЫБОРА ТОКЕНОВ ===
async def confirm_tokens(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    wallet_address = data.get("wallet_address")
    wallet_name = data.get("wallet_name")
    selected_tokens = data.get("selected_tokens", [])

    if not selected_tokens:
        await callback.answer("⚠️ Вы не выбрали ни одного токена!", show_alert=True)
        return

    db.add_wallet(wallet_address, wallet_name, ",".join(selected_tokens))
    await state.clear()
    await callback.message.edit_text("✅ Кошелек добавлен!", reply_markup=get_wallets_keyboard())

# === УДАЛЕНИЕ КОШЕЛЬКА ===
async def delete_wallet(callback: types.CallbackQuery):
    wallet_id = callback.data.split("_")[2]
    db.remove_wallet(wallet_id)
    await callback.message.edit_text("🗑 Кошелек удален!", reply_markup=get_wallets_keyboard())

# === ВОЗВРАТ В ГЛАВНОЕ МЕНЮ ===
async def go_home(callback: types.CallbackQuery):
    await callback.message.edit_text("🏠 Главное меню:", reply_markup=get_main_keyboard())

# === РЕГИСТРАЦИЯ ХЕНДЛЕРОВ ===
def register_handlers(dp: Dispatcher):
    dp.message.register(start_command, Command("start"))
    dp.callback_query.register(wallets_menu, F.data == "wallets_menu")
    dp.callback_query.register(wallet_callback, F.data.startswith("wallet_"))
    dp.callback_query.register(add_wallet_start, F.data == "add_wallet")
    dp.message.register(process_wallet_address, StateFilter(AddWalletState.address))
    dp.message.register(process_wallet_name, StateFilter(AddWalletState.name))
    dp.callback_query.register(toggle_token, F.data.startswith("toggle_token_"))
    dp.callback_query.register(confirm_tokens, F.data == "confirm_tokens")
    dp.callback_query.register(delete_wallet, F.data.startswith("delete_wallet_"))
    dp.callback_query.register(go_home, F.data == "home")
