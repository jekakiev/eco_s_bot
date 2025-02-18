import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command, Text
from database import Database
from threads_config import TOKEN_CONFIG

db = Database()

# Функція для створення клавіатури з гаманцями
def get_wallets_keyboard():
    builder = InlineKeyboardBuilder()
    wallets = db.get_wallets()
    
    for wallet in wallets:
        builder.button(text=wallet[1], callback_data=f"wallet_{wallet[0]}")  # wallet_id
    builder.button(text="⬅️ Повернутись на головну", callback_data="home")
    
    return builder.as_markup()

# Функція для створення меню керування гаманцем
def get_wallet_control_keyboard(wallet_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 Видалити", callback_data=f"delete_wallet_{wallet_id}")
    builder.button(text="🔄 Змінити монети", callback_data=f"edit_tokens_{wallet_id}")
    builder.button(text="✏️ Перейменувати", callback_data=f"rename_wallet_{wallet_id}")
    builder.button(text="⬅️ Повернутись на головну", callback_data="home")
    
    return builder.as_markup()

# Функція для створення клавіатури вибору токенів
def get_tokens_keyboard(selected_tokens):
    builder = InlineKeyboardBuilder()
    
    for token_name, config in TOKEN_CONFIG.items():
        is_selected = "✅ " if token_name in selected_tokens else ""
        builder.button(text=f"{is_selected}{token_name}", callback_data=f"toggle_token_{token_name}")

    builder.button(text="✅ Додати", callback_data="confirm_tokens")
    builder.button(text="⬅️ Повернутись на головну", callback_data="home")
    
    return builder.as_markup()

# Обробник команди /wallets
async def wallets_command(message: types.Message):
    await message.answer("📜 Список ваших гаманців:", reply_markup=get_wallets_keyboard())

# Обробник вибору гаманця
async def wallet_callback(callback: types.CallbackQuery):
    wallet_id = callback.data.split("_")[1]
    await callback.message.edit_text(f"⚙️ Керування гаманцем:", reply_markup=get_wallet_control_keyboard(wallet_id))

# Обробник кнопки "Додати гаманець"
async def add_wallet_start(callback: types.CallbackQuery, state: Dispatcher):
    await state.set_state("add_wallet_address")
    await callback.message.edit_text("📝 Введіть адресу гаманця:", reply_markup=get_cancel_keyboard())

# Обробник введення адреси
async def process_wallet_address(message: types.Message, state: Dispatcher):
    await state.update_data(wallet_address=message.text)
    await state.set_state("add_wallet_name")
    await message.answer("✏️ Введіть назву гаманця:", reply_markup=get_cancel_keyboard())

# Обробник введення імені
async def process_wallet_name(message: types.Message, state: Dispatcher):
    await state.update_data(wallet_name=message.text)
    await state.set_state("add_wallet_tokens")
    await message.answer("🪙 Виберіть монети для відстежування:", reply_markup=get_tokens_keyboard([]))

# Обробник вибору токенів
async def toggle_token(callback: types.CallbackQuery, state: Dispatcher):
    token = callback.data.split("_")[1]
    data = await state.get_data()
    selected_tokens = data.get("selected_tokens", [])

    if token in selected_tokens:
        selected_tokens.remove(token)
    else:
        selected_tokens.append(token)

    await state.update_data(selected_tokens=selected_tokens)
    await callback.message.edit_text("🪙 Виберіть монети для відстежування:", reply_markup=get_tokens_keyboard(selected_tokens))

# Підтвердження вибору токенів
async def confirm_tokens(callback: types.CallbackQuery, state: Dispatcher):
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

# Видалення гаманця
async def delete_wallet(callback: types.CallbackQuery):
    wallet_id = callback.data.split("_")[2]
    db.delete_wallet(wallet_id)
    await callback.message.edit_text("🗑 Гаманець видалено!", reply_markup=get_wallets_keyboard())

# Обробка повернення на головну
async def go_home(callback: types.CallbackQuery):
    await callback.message.edit_text("🏠 Головне меню:", reply_markup=get_main_keyboard())

# Реєстрація обробників
def register_handlers(dp: Dispatcher):
    dp.message.register(wallets_command, Command("wallets"))
    dp.callback_query.register(wallet_callback, Text(startswith="wallet_"))
    dp.callback_query.register(add_wallet_start, Text("add_wallet"))
    dp.message.register(process_wallet_address, state="add_wallet_address")
    dp.message.register(process_wallet_name, state="add_wallet_name")
    dp.callback_query.register(toggle_token, Text(startswith="toggle_token_"))
    dp.callback_query.register(confirm_tokens, Text("confirm_tokens"))
    dp.callback_query.register(delete_wallet, Text(startswith="delete_wallet_"))
    dp.callback_query.register(go_home, Text("home"))
