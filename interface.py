from aiogram import Dispatcher, types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram import F
from database import Database
from threads_config import TOKEN_CONFIG

db = Database()

# --- Головне меню ---
def get_main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📜 Показати гаманці", callback_data="wallets")
    builder.button(text="➕ Додати гаманець", callback_data="add_wallet")
    return builder.as_markup()

async def show_main_menu(message: types.Message):
    await message.answer("🏠 Головне меню:", reply_markup=get_main_keyboard())

# --- Клавіатури ---
def get_wallets_keyboard():
    builder = InlineKeyboardBuilder()
    wallets = db.get_all_wallets()

    for wallet in wallets:
        builder.button(text=wallet["name"], callback_data=f"wallet_{wallet['address']}")
    builder.button(text="⬅️ Повернутись на головну", callback_data="home")
    return builder.as_markup()

def get_wallet_control_keyboard(wallet_address):
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 Видалити", callback_data=f"delete_wallet_{wallet_address}")
    builder.button(text="🔄 Змінити монети", callback_data=f"edit_tokens_{wallet_address}")
    builder.button(text="✏️ Перейменувати", callback_data=f"rename_wallet_{wallet_address}")
    builder.button(text="⬅️ Повернутись на головну", callback_data="home")
    return builder.as_markup()

def get_tokens_keyboard(selected_tokens):
    builder = InlineKeyboardBuilder()
    for token_name in TOKEN_CONFIG.keys():
        is_selected = "✅ " if token_name in selected_tokens else ""
        builder.button(text=f"{is_selected}{token_name}", callback_data=f"toggle_token_{token_name}")
    builder.button(text="✅ Додати", callback_data="confirm_tokens")
    builder.button(text="⬅️ Повернутись на головну", callback_data="home")
    return builder.as_markup()

# --- Команда /wallets ---
async def wallets_command(message: types.Message):
    await message.answer("📜 Список ваших гаманців:", reply_markup=get_wallets_keyboard())

# --- Взаємодія з гаманцями ---
async def wallet_callback(callback: types.CallbackQuery):
    wallet_address = callback.data.split("_")[1]
    await callback.message.edit_text(f"⚙️ Керування гаманцем:", reply_markup=get_wallet_control_keyboard(wallet_address))

async def add_wallet_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state("add_wallet_address")
    await callback.message.edit_text("📝 Введіть адресу гаманця:")

async def process_wallet_address(message: types.Message, state: FSMContext):
    await state.update_data(wallet_address=message.text)
    await state.set_state("add_wallet_name")
    await message.answer("✏️ Введіть назву гаманця:")

async def process_wallet_name(message: types.Message, state: FSMContext):
    await state.update_data(wallet_name=message.text)
    await state.set_state("add_wallet_tokens")
    await message.answer("🪙 Виберіть монети для відстежування:", reply_markup=get_tokens_keyboard([]))

async def toggle_token(callback: types.CallbackQuery, state: FSMContext):
    token = callback.data.split("_")[1]
    data = await state.get_data()
    selected_tokens = data.get("selected_tokens", [])

    if token in selected_tokens:
        selected_tokens.remove(token)
    else:
        selected_tokens.append(token)

    await state.update_data(selected_tokens=selected_tokens)
    await callback.message.edit_text("🪙 Виберіть монети для відстежування:", reply_markup=get_tokens_keyboard(selected_tokens))

async def confirm_tokens(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    wallet_address = data.get("wallet_address")
    wallet_name = data.get("wallet_name")
    selected_tokens = data.get("selected_tokens", [])

    if not selected_tokens:
        await callback.answer("⚠️ Ви не обрали жодного токена!", show_alert=True)
        return

    db.add_wallet(wallet_address, wallet_name, ",".join(selected_tokens))
    await state.clear()
    await callback.message.edit_text("✅ Гаманець додано!", reply_markup=get_wallets_keyboard())

async def delete_wallet(callback: types.CallbackQuery):
    wallet_address = callback.data.split("_")[2]
    db.remove_wallet(wallet_address)
    await callback.message.edit_text("🗑 Гаманець видалено!", reply_markup=get_wallets_keyboard())

async def go_home(callback: types.CallbackQuery):
    await callback.message.edit_text("🏠 Головне меню:", reply_markup=get_main_keyboard())

# --- Реєстрація хендлерів ---
def register_handlers(dp: Dispatcher):
    dp.message.register(wallets_command, Command("wallets"))
    dp.message.register(show_main_menu, Command("start"))
    dp.callback_query.register(wallet_callback, F.data.startswith("wallet_"))
    dp.callback_query.register(add_wallet_start, F.data == "add_wallet")
    dp.message.register(process_wallet_address, state="add_wallet_address")
    dp.message.register(process_wallet_name, state="add_wallet_name")
    dp.callback_query.register(toggle_token, F.data.startswith("toggle_token_"))
    dp.callback_query.register(confirm_tokens, F.data == "confirm_tokens")
    dp.callback_query.register(delete_wallet, F.data.startswith("delete_wallet_"))
    dp.callback_query.register(go_home, F.data == "home")
