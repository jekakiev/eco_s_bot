from aiogram import types, Dispatcher, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from database import Database
from threads_config import TOKEN_CONFIG

db = Database()

# === СТАНИ ДЛЯ ДОДАВАННЯ ГАМАНЦЯ ===
class WalletStates(StatesGroup):
    waiting_for_address = State()
    waiting_for_name = State()
    waiting_for_tokens = State()

# === ГОЛОВНЕ МЕНЮ ===
def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="📜 Показати гаманці", callback_data="show_wallets")
    builder.button(text="➕ Додати гаманець", callback_data="add_wallet")
    return builder.as_markup()

# === КНОПКА НАЗАД ===
def get_back_button():
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ В головне меню", callback_data="home")
    return builder.as_markup()

# === СПИСОК ГАМАНЦІВ ===
def get_wallets_list():
    wallets = db.get_all_wallets()
    if not wallets:
        return "📭 У вас поки немає гаманців."

    text = "📜 *Ваші гаманці:*\n\n"
    for wallet in wallets:
        text += f"🔹 [{wallet['name'] or wallet['address'][:6] + '...'}](https://arbiscan.io/address/{wallet['address']})\n"

    return text

# === КЕРУВАННЯ ГАМАНЦЕМ ===
def get_wallet_control_keyboard(wallet_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 Видалити", callback_data=f"delete_wallet_{wallet_id}")
    builder.button(text="🔄 Змінити монети", callback_data=f"edit_tokens_{wallet_id}")
    builder.button(text="✏️ Перейменувати", callback_data=f"rename_wallet_{wallet_id}")
    builder.button(text="⬅️ В головне меню", callback_data="home")
    return builder.as_markup()

# === ВИБІР ТОКЕНІВ (2 В РЯД) ===
def get_tokens_keyboard(selected_tokens):
    builder = InlineKeyboardBuilder()
    
    for token_name in TOKEN_CONFIG:
        is_selected = "✅ " if token_name in selected_tokens else ""
        builder.button(text=f"{is_selected}{token_name}", callback_data=f"toggle_token_{token_name}")

    builder.adjust(2)
    builder.button(text="✅ Додати", callback_data="confirm_tokens")
    builder.button(text="⬅️ В головне меню", callback_data="home")
    
    return builder.as_markup()

# === ВІДОБРАЖЕННЯ СПИСКУ ГАМАНЦІВ ===
async def wallets_command(message: types.Message):
    await message.answer(get_wallets_list(), parse_mode="Markdown", disable_web_page_preview=True, reply_markup=get_main_menu())

# === ПОКАЗАТИ ГАМАНЦІ ===
async def show_wallets(callback: types.CallbackQuery):
    await callback.message.edit_text(get_wallets_list(), parse_mode="Markdown", disable_web_page_preview=True, reply_markup=get_main_menu())

# === ДОДАТИ ГАМАНЕЦЬ: ПОЧАТОК ===
async def add_wallet_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(WalletStates.waiting_for_address)
    await callback.message.edit_text("📝 Введіть адресу гаманця:", reply_markup=get_back_button())

# === ВВЕДЕННЯ АДРЕСИ ===
async def process_wallet_address(message: types.Message, state: FSMContext):
    await state.update_data(wallet_address=message.text)
    await state.set_state(WalletStates.waiting_for_name)
    await message.answer("✏️ Введіть назву гаманця:", reply_markup=get_back_button())

# === ВВЕДЕННЯ ІМЕНІ ===
async def process_wallet_name(message: types.Message, state: FSMContext):
    await state.update_data(wallet_name=message.text)
    await state.set_state(WalletStates.waiting_for_tokens)
    await message.answer("🪙 Виберіть монети для відстежування:", reply_markup=get_tokens_keyboard([]))

# === ВИБІР ТОКЕНІВ ===
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

# === ПІДТВЕРДЖЕННЯ ТОКЕНІВ ===
async def confirm_tokens(callback: types.CallbackQuery, state: FSMContext):
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

# === ВИДАЛЕННЯ ГАМАНЦЯ ===
async def delete_wallet(callback: types.CallbackQuery):
    wallet_id = callback.data.split("_")[2]
    db.remove_wallet(wallet_id)
    await callback.message.edit_text("🗑 Гаманець видалено!", reply_markup=get_main_menu())

# === ГОЛОВНЕ МЕНЮ ===
async def go_home(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🏠 Головне меню:", reply_markup=get_main_menu())

# === РЕЄСТРАЦІЯ ОБРОБНИКІВ ===
def register_handlers(dp: Dispatcher):
    dp.message.register(wallets_command, Command("wallets"))
    dp.callback_query.register(show_wallets, F.data == "show_wallets")
    dp.callback_query.register(add_wallet_start, F.data == "add_wallet")
    dp.message.register(process_wallet_address, WalletStates.waiting_for_address)
    dp.message.register(process_wallet_name, WalletStates.waiting_for_name)
    dp.callback_query.register(toggle_token, F.data.startswith("toggle_token_"))
    dp.callback_query.register(confirm_tokens, F.data == "confirm_tokens")
    dp.callback_query.register(delete_wallet, F.data.startswith("delete_wallet_"))
    dp.callback_query.register(go_home, F.data == "home")
