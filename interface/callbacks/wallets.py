from aiogram import types
from aiogram.fsm.context import FSMContext
from ..keyboards import get_wallets_list, get_back_button, get_tokens_keyboard, get_wallet_control_keyboard, get_main_menu
from ..states import WalletStates
from database import Database
from utils.logger_config import logger

db = Database()

async def show_wallets(callback: types.CallbackQuery):
    logger.info(f"Callback 'show_wallets' получен от {callback.from_user.id}")
    if int(db.get_setting("INTERFACE_INFO") or 0):
        logger.info("Кнопка 'Показать кошельки' нажата")
    try:
        text, reply_markup = get_wallets_list()
        await callback.message.answer(text, disable_web_page_preview=True, reply_markup=reply_markup)
        await callback.answer()
    except Exception as e:
        if int(db.get_setting("API_ERRORS") or 1):
            logger.error(f"Ошибка при отправке списка кошельков: {str(e)}")
        await callback.message.answer("❌ Произошла ошибка.", reply_markup=get_back_button())
        await callback.answer()

async def add_wallet_start(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Callback 'add_wallet' получен от {callback.from_user.id}")
    if int(db.get_setting("INTERFACE_INFO") or 0):
        logger.info("Кнопка 'Добавить кошелек' нажата")
    await state.set_state(WalletStates.waiting_for_address)
    await callback.message.edit_text("📝 Введите адрес кошелька:", reply_markup=get_back_button())
    await callback.answer()

async def process_wallet_address(message: types.Message, state: FSMContext):
    logger.info(f"Сообщение с адресом кошелька от {message.from_user.id}: {message.text}")
    if int(db.get_setting("INTERFACE_INFO") or 0):
        logger.info(f"Введен адрес кошелька: {message.text}")
    await state.update_data(wallet_address=message.text)
    await state.set_state(WalletStates.waiting_for_name)
    await message.answer("✏️ Введите название кошелька:", reply_markup=get_back_button())

async def process_wallet_name(message: types.Message, state: FSMContext):
    logger.info(f"Сообщение с именем кошелька от {message.from_user.id}: {message.text}")
    if int(db.get_setting("INTERFACE_INFO") or 0):
        logger.info(f"Введено имя кошелька: {message.text}")
    await state.update_data(wallet_name=message.text)
    await state.set_state(WalletStates.waiting_for_tokens)
    await state.update_data(selected_tokens=[])
    await message.answer("🪙 Выберите монеты для отслеживания:", reply_markup=get_tokens_keyboard([], is_edit=False))

async def toggle_token(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Callback 'toggle_token' получен от {callback.from_user.id}")
    token = callback.data.split("_")[2]
    if int(db.get_setting("INTERFACE_INFO") or 0):
        logger.info(f"Выбор токена: {token}")
    data = await state.get_data()
    selected_tokens = data.get("selected_tokens", [])

    if token in selected_tokens:
        selected_tokens.remove(token)
    else:
        selected_tokens.append(token)

    await state.update_data(selected_tokens=selected_tokens)
    is_edit = "wallet_id" in data
    await callback.message.edit_reply_markup(reply_markup=get_tokens_keyboard(selected_tokens, is_edit=is_edit))
    await callback.answer()

async def confirm_tokens(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Callback 'confirm_tokens' получен от {callback.from_user.id}")
    if int(db.get_setting("INTERFACE_INFO") or 0):
        logger.info("Подтверждение выбора токенов")
    data = await state.get_data()
    wallet_address = data.get("wallet_address")
    wallet_name = data.get("wallet_name")
    selected_tokens = data.get("selected_tokens", [])

    if not selected_tokens:
        await callback.answer("⚠️ Вы не выбрали ни одной монеты!", show_alert=True)
        return

    db.add_wallet(wallet_address, wallet_name, ",".join(selected_tokens))
    await state.clear()
    await callback.message.edit_text("✅ Кошелек добавлен!", reply_markup=get_main_menu())
    await callback.answer()

async def save_tokens(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Callback 'save_tokens' получен от {callback.from_user.id}")
    if int(db.get_setting("INTERFACE_INFO") or 0):
        logger.info("Сохранение токенов для кошелька")
    data = await state.get_data()
    wallet_id = data.get("wallet_id")
    selected_tokens = data.get("selected_tokens", [])

    if not selected_tokens:
        await callback.answer("⚠️ Вы не выбрали ни одной монеты!", show_alert=True)
        return

    db.update_wallet_tokens(wallet_id, ",".join(selected_tokens))
    wallet = db.get_wallet_by_id(wallet_id)
    text = f"✅ Токены обновлены!\n_________\nИмя кошелька: {wallet['name']}\nАдрес кошелька: {wallet['address']}"
    await state.clear()
    await callback.message.edit_text(text, reply_markup=get_wallet_control_keyboard(wallet_id))
    await callback.answer()

async def delete_wallet(callback: types.CallbackQuery):
    logger.info(f"Callback 'delete_wallet' получен от {callback.from_user.id}")
    wallet_id = callback.data.split("_")[2]
    if int(db.get_setting("INTERFACE_INFO") or 0):
        logger.info(f"Удаление кошелька с ID {wallet_id}")
    db.remove_wallet(wallet_id)
    await callback.message.edit_text("🗑 Кошелек удалён!", reply_markup=get_main_menu())
    await callback.answer()

async def rename_wallet_start(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Callback 'rename_wallet' получен от {callback.from_user.id}")
    wallet_id = callback.data.split("_")[2]
    if int(db.get_setting("INTERFACE_INFO") or 0):
        logger.info(f"Начало переименования кошелька с ID {wallet_id}")
    await state.update_data(wallet_id=wallet_id)
    await state.set_state(WalletStates.waiting_for_new_name)
    await callback.message.edit_text("✏️ Введите новое имя кошелька:", reply_markup=get_back_button())
    await callback.answer()

async def process_new_wallet_name(message: types.Message, state: FSMContext):
    logger.info(f"Сообщение с новым именем кошелька от {message.from_user.id}: {message.text}")
    if int(db.get_setting("INTERFACE_INFO") or 0):
        logger.info(f"Введено новое имя кошелька: {message.text}")
    data = await state.get_data()
    wallet_id = data.get("wallet_id")
    new_name = message.text
    db.update_wallet_name(wallet_id, new_name)
    wallet = db.get_wallet_by_id(wallet_id)
    text = f"✅ Имя кошелька обновлено на: {new_name}\n_________\nИмя кошелька: {wallet['name']}\nАдрес кошелька: {wallet['address']}"
    await state.clear()
    await message.answer(text, reply_markup=get_wallet_control_keyboard(wallet_id))

async def edit_tokens_start(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Callback 'edit_tokens' получен от {callback.from_user.id}")
    wallet_id = callback.data.split("_")[2]
    if int(db.get_setting("INTERFACE_INFO") or 0):
        logger.info(f"Начало редактирования токенов для кошелька с ID {wallet_id}")
    wallet = db.get_wallet_by_id(wallet_id)
    current_tokens = wallet["tokens"].split(",") if wallet["tokens"] else []
    await state.update_data(wallet_id=wallet_id, selected_tokens=current_tokens)
    await callback.message.edit_text("🪙 Выберите монеты для отслеживания:", reply_markup=get_tokens_keyboard(current_tokens, is_edit=True))
    await callback.answer()