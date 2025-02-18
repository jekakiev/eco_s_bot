from aiogram import types, Dispatcher, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from database import Database
from threads_config import TOKEN_CONFIG

db = Database()

# Головне меню
def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="📜 Показати гаманці", callback_data="show_wallets")
    builder.button(text="➕ Додати гаманець", callback_data="add_wallet")
    return builder.as_markup()

# Кнопка "Назад"
def get_back_button():
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ В головне меню", callback_data="home")
    return builder.as_markup()

# Список гаманців (гіперпосиланнями)
def get_wallets_list():
    wallets = db.get_all_wallets()
    if not wallets:
        return "📭 У вас поки немає гаманців."

    text = "📜 *Ваші гаманці:*\n\n"
    for wallet in wallets:
        text += f"🔹 [{wallet['name'] or wallet['address'][:6] + '...'}](https://arbiscan.io/address/{wallet['address']})\n"

    return text

# Меню керування гаманцем
def get_wallet_control_keyboard(wallet_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 Видалити", callback_data=f"delete_wallet_{wallet_id}")
    builder.button(text="🔄 Змінити монети", callback_data=f"edit_tokens_{wallet_id}")
    builder.button(text="✏️ Перейменувати", callback_data=f"rename_wallet_{wallet_id}")
    builder.button(text="⬅️ В головне меню", callback_data="home")
    return builder.as_markup()

# Вибір токенів (2 кнопки в ряд)
def get_tokens_keyboard(selected_tokens):
    builder = InlineKeyboardBuilder()
    
    for token_name, config in TOKEN_CONFIG.items():
        is_selected = "✅ " if token_name in selected_tokens else ""
        builder.button(text=f"{is_selected}{token_name}", callback_data=f"toggle_token_{token_name}")

    builder.adjust(2)  # Дві кнопки в ряд
    builder.button(text="✅ Додати", callback_data="confirm_tokens")
    builder.button(text="⬅️ В головне меню", callback_data="home")
    
    return builder.as_markup()

# Обробник команди /wallets
async def wallets_command(message: types.Message):
    await message.answer(get_wallets_list(), parse_mode="Markdown", disable_web_page_preview=True, reply_markup=get_main_menu())

# Обробник кнопки "Показати гаманці"
async def show_wallets(callback: types.CallbackQuery):
    await callback.message.edit_text(get_wallets_list(), parse_mode="Markdown", disable_web_page_preview=True, reply_markup=get_main_menu())

# Обробник кнопки "Додати гаманець"
async def add_wallet_start(callback: types.CallbackQuery, state: Dispatcher):
    await state.set_state("add_wallet_address")
    await callback.message.edit_text("📝 Введіть адресу гаманця:", reply_markup=get_back_button())

# Введення адреси
async def process_wallet_address(message: types.Message, state: Dispatcher):
    await state.update_data(wallet_address=message.text)
    await state.set_state("add_wallet_name")
    await message.answer("✏️ Введіть назву гаманця:", reply_markup=get_back_button())

# Введення імені
async def process_wallet_name(message: types.Message, state: Dispatcher):
    await state.update_data(wallet_name=message.text)
    await state.set_state("add_wallet_tokens")
    await message.answer("🪙 Виберіть монети для відстежування:", reply_markup=get_tokens_keyboard([]))

# Вибір токенів
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
        await callback.answer("⚠️ Ви не вибрали жодного токена!", show_alert=True)
        return

    db.add_wallet(wallet_address, wallet_name, ",".join(selected_tokens))
    await state.clear()
    await callback.message.edit_text("✅ Гаманець додано!", reply_markup=get_main_menu())

# Видалення гаманця
async def delete_wallet(callback: types.CallbackQuery):
    wallet_id = callback.data.split("_")[2]
    db.remove_wallet(wallet_id)
    await callback.message.edit_text("🗑 Гаманець видалено!", reply_markup=get_main_menu())

# Обробник "В головне меню"
async def go_home(callback: types.CallbackQuery):
    await callback.message.edit_text("🏠 Головне меню:", reply_markup=get_main_menu())

# Реєстрація обробників
def register_handlers(dp: Dispatcher):
    dp.message.register(wallets_command, Command("wallets"))
    dp.callback_query.register(show_wallets, F.data == "show_wallets")
    dp.callback_query.register(add_wallet_start, F.data == "add_wallet")
    dp.message.register(process_wallet_address, F.state == "add_wallet_address")
    dp.message.register(process_wallet_name, F.state == "add_wallet_name")
    dp.callback_query.register(toggle_token, F.data.startswith("toggle_token_"))
    dp.callback_query.register(confirm_tokens, F.data == "confirm_tokens")
    dp.callback_query.register(delete_wallet, F.data.startswith("delete_wallet_"))
    dp.callback_query.register(go_home, F.data == "home")
