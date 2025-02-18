import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from database import Database
from threads_config import TOKEN_CONFIG

db = Database()


# ==== Машина состояний для добавления кошелька ====
class WalletState(StatesGroup):
    waiting_for_address = State()
    waiting_for_name = State()
    waiting_for_tokens = State()


# ==== Функция для создания главного меню ====
def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="📜 Показать кошельки", callback_data="show_wallets")
    builder.button(text="➕ Добавить кошелек", callback_data="add_wallet")
    return builder.as_markup()


# ==== Функция для отображения списка кошельков ====
async def show_wallets(callback: types.CallbackQuery):
    wallets = db.get_all_wallets()
    if not wallets:
        await callback.message.edit_text("⚠️ У вас пока нет добавленных кошельков.", reply_markup=get_main_menu())
        return

    text = "📜 <b>Ваши кошельки:</b>\n\n"
    for wallet in wallets:
        text += f"🔹 <a href='https://arbiscan.io/address/{wallet['address']}'>{wallet['name']}</a>\n"

    text += "\nВыберите кошелек для управления ⬇️"
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_wallets_keyboard(wallets))


# ==== Функция для создания кнопок управления кошельком ====
def get_wallets_keyboard(wallets):
    builder = InlineKeyboardBuilder()
    for wallet in wallets:
        builder.button(text=f"⚙️ {wallet['name']}", callback_data=f"wallet_{wallet['id']}")
    builder.button(text="⬅️ Назад", callback_data="home")
    return builder.as_markup()


# ==== Функция для управления кошельком ====
async def wallet_control(callback: types.CallbackQuery):
    wallet_id = callback.data.split("_")[1]
    wallet = db.get_wallet_by_id(wallet_id)

    if not wallet:
        await callback.message.edit_text("⚠️ Кошелек не найден!", reply_markup=get_main_menu())
        return

    text = f"⚙️ <b>Управление кошельком</b>\n\n"
    text += f"📍 <b>Название:</b> {wallet['name']}\n"
    text += f"💳 <b>Адрес:</b> <a href='https://arbiscan.io/address/{wallet['address']}'>{wallet['address']}</a>\n"
    text += f"🪙 <b>Отслеживаемые токены:</b> {wallet['tokens'] if wallet['tokens'] else 'Нет'}\n"

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_wallet_control_keyboard(wallet_id))


# ==== Функция для кнопок управления конкретным кошельком ====
def get_wallet_control_keyboard(wallet_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 Удалить", callback_data=f"delete_wallet_{wallet_id}")
    builder.button(text="🔄 Изменить токены", callback_data=f"edit_tokens_{wallet_id}")
    builder.button(text="✏️ Переименовать", callback_data=f"rename_wallet_{wallet_id}")
    builder.button(text="⬅️ Назад", callback_data="show_wallets")
    return builder.as_markup()


# ==== Начало добавления кошелька ====
async def add_wallet_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(WalletState.waiting_for_address)
    await callback.message.edit_text("📝 Введите адрес кошелька:", reply_markup=get_cancel_keyboard())


# ==== Ввод адреса кошелька ====
async def process_wallet_address(message: types.Message, state: FSMContext):
    await state.update_data(wallet_address=message.text)
    await state.set_state(WalletState.waiting_for_name)
    await message.answer("✏️ Введите название кошелька:", reply_markup=get_cancel_keyboard())


# ==== Ввод имени кошелька ====
async def process_wallet_name(message: types.Message, state: FSMContext):
    await state.update_data(wallet_name=message.text)
    await state.set_state(WalletState.waiting_for_tokens)
    await message.answer("🪙 Выберите токены для отслеживания:", reply_markup=get_tokens_keyboard([]))


# ==== Выбор токенов (работает как галочки) ====
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


# ==== Подтверждение выбора токенов ====
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


# ==== Удаление кошелька ====
async def delete_wallet(callback: types.CallbackQuery):
    wallet_id = callback.data.split("_")[2]
    db.remove_wallet(wallet_id)
    await callback.message.edit_text("🗑 Кошелек удален!", reply_markup=get_main_menu())


# ==== Отмена операции ====
async def cancel_operation(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🚫 Операция отменена!", reply_markup=get_main_menu())


# ==== Функция для кнопок отмены ====
def get_cancel_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="cancel")
    return builder.as_markup()


# ==== Функция для создания клавиатуры выбора токенов (в два ряда) ====
def get_tokens_keyboard(selected_tokens):
    builder = InlineKeyboardBuilder()
    buttons = []

    for token_name, config in TOKEN_CONFIG.items():
        is_selected = "✅ " if token_name in selected_tokens else ""
        buttons.append(types.InlineKeyboardButton(text=f"{is_selected}{token_name}", callback_data=f"toggle_token_{token_name}"))

    # Делаем кнопки в два ряда
    for i in range(0, len(buttons), 2):
        builder.row(*buttons[i:i+2])

    builder.button(text="✅ Добавить", callback_data="confirm_tokens")
    builder.button(text="❌ Отмена", callback_data="cancel")

    return builder.as_markup()


# ==== Регистрация обработчиков ====
def register_handlers(dp: Dispatcher):
    dp.message.register(wallet_control, Command("wallets"))
    dp.message.register(process_wallet_address, WalletState.waiting_for_address)
    dp.message.register(process_wallet_name, WalletState.waiting_for_name)
    dp.callback_query.register(toggle_token, CallbackData.filter("toggle_token_"))
    dp.callback_query.register(confirm_tokens, CallbackData.filter("confirm_tokens"))
    dp.callback_query.register(delete_wallet, CallbackData.filter("delete_wallet_"))
    dp.callback_query.register(cancel_operation, CallbackData.filter("cancel"))
    dp.callback_query.register(add_wallet_start, CallbackData.filter("add_wallet"))
    dp.callback_query.register(show_wallets, CallbackData.filter("show_wallets"))
