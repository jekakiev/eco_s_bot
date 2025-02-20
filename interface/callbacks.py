from aiogram import types
from aiogram.fsm.context import FSMContext
from .keyboards import get_main_menu, get_back_button, get_tokens_keyboard, get_wallet_control_keyboard, get_wallets_list
from .states import WalletStates
from database import Database

db = Database()

# === ПОКАЗАТЬ КОШЕЛЬКИ ===
async def show_wallets(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить кошелек", callback_data="add_wallet")
    builder.button(text="⬅️ Назад", callback_data="home")
    await callback.message.edit_text(get_wallets_list(), parse_mode="Markdown", disable_web_page_preview=True, reply_markup=builder.as_markup())

# === ДОБАВЛЕНИЕ КОШЕЛЬКА: НАЧАЛО ===
async def add_wallet_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(WalletStates.waiting_for_address)
    await callback.message.edit_text("📝 Введите адрес кошелька:", reply_markup=get_back_button())

# === ВВОД АДРЕСА ===
async def process_wallet_address(message: types.Message, state: FSMContext):
    await state.update_data(wallet_address=message.text)
    await state.set_state(WalletStates.waiting_for_name)
    await message.answer("✏️ Введите название кошелька:", reply_markup=get_back_button())

# === ВВОД ИМЕНИ ===
async def process_wallet_name(message: types.Message, state: FSMContext):
    await state.update_data(wallet_name=message.text)
    await state.set_state(WalletStates.waiting_for_tokens)
    await state.update_data(selected_tokens=[])  # Очищаем выбранные токены
    await message.answer("🪙 Выберите монеты для отслеживания:", reply_markup=get_tokens_keyboard([]))

# === ВЫБОР ТОКЕНОВ ===
async def toggle_token(callback: types.CallbackQuery, state: FSMContext):
    token = callback.data.split("_")[2]
    data = await state.get_data()
    selected_tokens = data.get("selected_tokens", [])

    if token in selected_tokens:
        selected_tokens.remove(token)
    else:
        selected_tokens.append(token)

    await state.update_data(selected_tokens=selected_tokens)

    # Обновляем только клавиатуру, без изменения текста
    await callback.message.edit_reply_markup(reply_markup=get_tokens_keyboard(selected_tokens))

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
    await callback.message.edit_text("✅ Кошелек добавлен!", reply_markup=get_main_menu())

# === УДАЛЕНИЕ КОШЕЛЬКА ===
async def delete_wallet(callback: types.CallbackQuery):
    wallet_id = callback.data.split("_")[2]
    db.remove_wallet(wallet_id)
    await callback.message.edit_text("🗑 Кошелек удален!", reply_markup=get_main_menu())

# === ПЕРЕИМЕНОВАНИЕ КОШЕЛЬКА ===
async def rename_wallet_start(callback: types.CallbackQuery, state: FSMContext):
    wallet_id = callback.data.split("_")[2]
    await state.update_data(wallet_id=wallet_id)
    await state.set_state(WalletStates.waiting_for_new_name)
    await callback.message.edit_text("✏️ Введите новое имя кошелька:", reply_markup=get_back_button())

async def process_new_wallet_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    wallet_id = data.get("wallet_id")
    new_name = message.text
    db.update_wallet_name(wallet_id, new_name)
    await state.clear()
    await message.answer(f"✅ Имя кошелька обновлено на: {new_name}", reply_markup=get_main_menu())

# === РЕДАКТИРОВАНИЕ КОШЕЛЬКА ===
async def edit_wallet(callback: types.CallbackQuery):
    wallet_id = callback.data.split("_")[1]
    wallet = db.get_wallet_by_id(wallet_id)
    text = f"Имя кошелька: {wallet['name']}\nАдрес кошелька: {wallet['address']}"
    await callback.message.edit_text(text, reply_markup=get_wallet_control_keyboard(wallet_id))

# === ГЛАВНОЕ МЕНЮ ===
async def go_home(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🏠 Главное меню:", reply_markup=get_main_menu())
