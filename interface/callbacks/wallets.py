# /interface/callbacks/wallets.py
from aiogram import types
from aiogram.fsm.context import FSMContext
from ..keyboards import get_main_menu, get_back_button, get_tokens_keyboard, get_wallet_control_keyboard
from ..states import WalletStates
from app_config import db
from utils.logger_config import logger, should_log

async def show_wallets(callback: types.CallbackQuery, state: FSMContext):
    if should_log("interface"):
        logger.info(f"Callback 'show_wallets' получен от {callback.from_user.id}")
        logger.info("Кнопка 'Показать кошельки' нажата")
    text, reply_markup = get_wallets_list()
    await callback.message.answer(text, disable_web_page_preview=True, reply_markup=reply_markup)
    await callback.answer()

async def add_wallet_start(callback: types.CallbackQuery, state: FSMContext):
    if should_log("interface"):
        logger.info(f"Callback 'add_wallet' получен от {callback.from_user.id}")
        logger.info("Кнопка 'Добавить кошелек' нажата")
    await state.set_state(WalletStates.waiting_for_address)
    await callback.message.edit_text("📝 Введите адрес кошелька:", reply_markup=get_back_button())
    await callback.answer()

async def process_wallet_address(message: types.Message, state: FSMContext):
    if should_log("interface"):
        logger.info(f"Сообщение с адресом кошелька от {message.from_user.id}: {message.text}")
        logger.info(f"Введен адрес кошелька: {message.text}")
    address = message.text.strip()
    if not address.startswith("0x") or len(address) != 42:
        await message.answer("❌ Неверный формат адреса. Введите адрес в формате 0x... (42 символа).", reply_markup=get_back_button())
        return
    await state.update_data(wallet_address=address)
    sent_message = await message.answer("📝 Введите имя кошелька:", reply_markup=get_back_button())
    await message.delete()
    await state.set_state(WalletStates.waiting_for_name)

async def process_wallet_name(message: types.Message, state: FSMContext):
    if should_log("interface"):
        logger.info(f"Сообщение с именем кошелька от {message.from_user.id}: {message.text}")
        logger.info(f"Введено имя кошелька: {message.text}")
    name = message.text.strip()
    if not name:
        sent_message = await message.answer("❌ Имя не может быть пустым.", reply_markup=get_back_button())
        await message.delete()
        return
    user_data = await state.get_data()
    address = user_data["wallet_address"]
    existing_wallet = db.wallets.get_wallet_by_address(address)
    if existing_wallet:
        sent_message = await message.answer("❌ Такой кошелек уже существует!", reply_markup=get_back_button())
        await message.delete()
        await state.clear()
        return
    await state.update_data(wallet_name=name)
    await state.set_state(WalletStates.waiting_for_tokens)
    await state.update_data(selected_tokens=[])
    tracked_tokens = [token[2] for token in db.tracked_tokens.get_all_tracked_tokens()]
    if should_log("debug"):
        logger.debug(f"Токены из базы для выбора: {tracked_tokens}")
    if not tracked_tokens:
        sent_message = await message.answer("🪙 Токены для отслеживания ещё не добавлены. Добавьте токены через меню 'Показать токены' -> 'Добавить токен'.", reply_markup=get_main_menu())
        await message.delete()
        await state.clear()
    else:
        sent_message = await message.answer("🪙 Выберите монеты для отслеживания:", reply_markup=get_tokens_keyboard([], is_edit=False))
        await message.delete()

async def toggle_token(callback: types.CallbackQuery, state: FSMContext):
    if should_log("interface"):
        logger.info(f"Callback 'toggle_token' получен от {callback.from_user.id}: {callback.data}")
        logger.info(f"Переключение токена: {callback.data}")
    token = callback.data.replace("toggle_token_", "")
    user_data = await state.get_data()
    selected_tokens = user_data.get("selected_tokens", [])
    if should_log("debug"):
        logger.debug(f"Текущие выбранные токены: {selected_tokens}, новый токен: {token}")
    if token in selected_tokens:
        selected_tokens.remove(token)
    else:
        selected_tokens.append(token)
    await state.update_data(selected_tokens=selected_tokens)
    is_edit = "wallet_id" in user_data
    await callback.message.edit_reply_markup(reply_markup=get_tokens_keyboard(selected_tokens, is_edit=is_edit))
    await callback.answer()

async def confirm_tokens(callback: types.CallbackQuery, state: FSMContext):
    if should_log("interface"):
        logger.info(f"Callback 'confirm_tokens' получен от {callback.from_user.id}")
        logger.info("Подтверждение токенов нажато")
    data = await state.get_data()
    wallet_address = data.get("wallet_address")
    wallet_name = data.get("wallet_name")
    selected_tokens = data.get("selected_tokens", [])
    if should_log("debug"):
        logger.debug(f"Подтвержденные токены для кошелька {wallet_name}: {selected_tokens}")
    if not selected_tokens:
        await callback.answer("⚠️ Вы не выбрали ни одной монеты!", show_alert=True)
        return
    db.reconnect()
    wallet_id = db.wallets.add_wallet(wallet_address, wallet_name, ",".join(selected_tokens))
    last_4 = wallet_address[-4:]
    if should_log("debug"):
        logger.debug(f"Добавлен кошелек с адресом {wallet_address}, команда: /Editw_{last_4}, список кошельков после добавления: {db.wallets.get_all_wallets()}")
    await state.clear()
    sent_message = await callback.message.edit_text(f"✅ Кошелек {wallet_name} ({last_4}) добавлен! Используйте /Editw_{last_4} для редактирования.", reply_markup=get_main_menu())
    await callback.answer()

async def save_tokens(callback: types.CallbackQuery, state: FSMContext):
    if should_log("interface"):
        logger.info(f"Callback 'save_tokens' получен от {callback.from_user.id}")
        logger.info("Сохранение токенов нажато")
    data = await state.get_data()
    wallet_id = data.get("wallet_id")
    selected_tokens = data.get("selected_tokens", [])
    if should_log("debug"):
        logger.debug(f"Сохраненные токены для кошелька с ID {wallet_id}: {selected_tokens}")
    if not selected_tokens:
        await callback.answer("⚠️ Вы не выбрали ни одной монеты!", show_alert=True)
        return
    db.wallets.update_wallet_tokens(wallet_id, ",".join(selected_tokens))
    wallet = db.wallets.get_wallet_by_id(wallet_id)
    last_4 = wallet[1][-4:]
    text = f"✅ Токены обновлены!\nКошелек: {wallet[2]} ({last_4})"
    await state.clear()
    sent_message = await callback.message.edit_text(text, reply_markup=get_wallet_control_keyboard(wallet_id))
    await callback.answer()

async def delete_wallet(callback: types.CallbackQuery, state: FSMContext):
    if should_log("interface"):
        logger.info(f"Callback 'delete_wallet' получен от {callback.from_user.id}: {callback.data}")
        logger.info(f"Удаление кошелька: {callback.data}")
    wallet_id = int(callback.data.replace("delete_wallet_", ""))
    if should_log("debug"):
        logger.debug(f"Попытка удаления кошелька с ID: {wallet_id}")
    db.reconnect()
    wallet = db.wallets.get_wallet_by_id(wallet_id)
    if not wallet:
        if should_log("debug"):
            logger.debug(f"Кошелек с ID {wallet_id} не найден в базе: {db.wallets.get_all_wallets()}")
        await callback.answer("❌ Кошелек не найден!", show_alert=True)
        return
    db.wallets.delete_wallet(wallet_id)
    text, reply_markup = get_wallets_list()
    sent_message = await callback.message.edit_text(text, reply_markup=reply_markup, disable_web_page_preview=True)
    await callback.answer(f"🗑 Кошелек {wallet[2]} удален!")

async def rename_wallet_start(callback: types.CallbackQuery, state: FSMContext):
    if should_log("interface"):
        logger.info(f"Callback 'rename_wallet' получен от {callback.from_user.id}: {callback.data}")
        logger.info(f"Переименование кошелька: {callback.data}")
    wallet_id = int(callback.data.replace("rename_wallet_", ""))
    db.reconnect()
    wallet = db.wallets.get_wallet_by_id(wallet_id)
    if not wallet:
        await callback.answer("❌ Кошелек не найден!", show_alert=True)
        return
    await state.update_data(wallet_id=wallet_id)
    await state.set_state(WalletStates.waiting_for_new_name)
    await callback.message.edit_text(f"📝 Введите новое имя для кошелька {wallet[2]}:", reply_markup=get_back_button())
    await callback.answer()

async def process_new_wallet_name(message: types.Message, state: FSMContext):
    if should_log("interface"):
        logger.info(f"Сообщение с новым именем кошелька от {message.from_user.id}: {message.text}")
        logger.info(f"Введено новое имя кошелька: {message.text}")
    new_name = message.text.strip()
    if not new_name:
        sent_message = await message.answer("❌ Имя не может быть пустым.", reply_markup=get_back_button())
        await message.delete()
        return
    user_data = await state.get_data()
    wallet_id = user_data["wallet_id"]
    db.reconnect()
    wallet = db.wallets.get_wallet_by_id(wallet_id)
    if not wallet:
        sent_message = await message.answer("❌ Кошелек не найден!", reply_markup=get_back_button())
        await message.delete()
        await state.clear()
        return
    db.wallets.rename_wallet(wallet_id, new_name)
    sent_message = await message.answer(f"💰 Кошелек переименован в {new_name}!", reply_markup=get_wallet_control_keyboard(wallet_id))
    await message.delete()
    await state.clear()

async def edit_tokens_start(callback: types.CallbackQuery, state: FSMContext):
    if should_log("interface"):
        logger.info(f"Callback 'edit_tokens' получен от {callback.from_user.id}: {callback.data}")
        logger.info(f"Редактирование токенов для кошелька: {callback.data}")
    wallet_id = int(callback.data.replace("edit_tokens_", ""))
    db.reconnect()
    wallet = db.wallets.get_wallet_by_id(wallet_id)
    if not wallet:
        if should_log("debug"):
            logger.debug(f"Кошелек с ID {wallet_id} не найден в базе: {db.wallets.get_all_wallets()}")
        await callback.answer("❌ Кошелек не найден!", show_alert=True)
        return
    tokens = wallet[3].split(",") if wallet[3] else []
    tracked_tokens = [token[2] for token in db.tracked_tokens.get_all_tracked_tokens()]
    if should_log("debug"):
        logger.debug(f"Токены из базы для редактирования: {tracked_tokens}, текущие токены кошелька: {tokens}")
    if not tracked_tokens:
        sent_message = await callback.message.edit_text("🪙 Токены для отслеживания ещё не добавлены. Добавьте токены через меню 'Показать токены' -> 'Добавить токен'.", reply_markup=get_main_menu())
        await callback.answer()
        await state.clear()
    else:
        text = f"Кошелек: {wallet[2]} ({wallet[1][-4:]})"
        sent_message = await callback.message.edit_text(f"🪙 Выберите токены для кошелька {wallet[2]} ({wallet[1][-4:]}):", reply_markup=get_tokens_keyboard(tokens, is_edit=True))
        await state.set_state(WalletStates.waiting_for_tokens)
        await callback.answer()