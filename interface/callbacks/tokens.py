# /interface/callbacks/tokens.py
from aiogram import types
from aiogram.fsm.context import FSMContext
from ..keyboards import get_main_menu, get_tracked_tokens_list, get_token_control_keyboard, get_token_name_confirmation_keyboard, get_thread_confirmation_keyboard, get_back_button
from ..states import TokenStates
from app_config import db
from utils.logger_config import logger, should_log
from utils.arbiscan import get_token_info
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

logger.info("Загружена версия /interface/callbacks/tokens.py с исправлением edit_token_thread (v2.12)")

async def show_tokens(callback: types.CallbackQuery, state: FSMContext):
    if should_log("interface"):
        logger.info(f"Callback 'show_tokens' получен от {callback.from_user.id}")
        logger.info("Кнопка 'Показать токены' нажата")
    text, reply_markup = get_tracked_tokens_list()
    await callback.message.edit_text(text, reply_markup=reply_markup, disable_web_page_preview=True)
    await callback.answer()

async def add_token_start(callback: types.CallbackQuery, state: FSMContext):
    if should_log("interface"):
        logger.info(f"Callback 'add_token' получен от {callback.from_user.id}")
        logger.info("Кнопка 'Добавить токен' нажата")
    await callback.message.edit_text("📝 Введите адрес контракта токена (например, 0x...):", reply_markup=get_back_button())
    await state.set_state(TokenStates.waiting_for_contract_address)
    await callback.answer()

async def process_contract_address(message: types.Message, state: FSMContext):
    if should_log("interface"):
        logger.info(f"Сообщение с адресом контракта токена от {message.from_user.id}: {message.text}")
        logger.info(f"Введен адрес контракта токена: {message.text}")
    contract_address = message.text.strip()
    if not contract_address.startswith("0x") or len(contract_address) != 42:
        await message.answer("❌ Неверный формат адреса. Введите адрес в формате 0x... (42 символа).", reply_markup=get_back_button())
        return
    existing_tokens = db.tracked_tokens.get_all_tracked_tokens()
    if any(token[1].lower() == contract_address.lower() for token in existing_tokens):
        await message.answer("❌ Такой токен уже отслеживается!", reply_markup=get_back_button())
        await state.clear()
        return
    await state.update_data(contract_address=contract_address)
    token_info = await get_token_info(contract_address)
    logger.debug(f"Данные токена от Arbiscan для {contract_address}: {token_info}")
    token_name = token_info["tokenSymbol"] if token_info["tokenSymbol"] and token_info["tokenSymbol"] != "Неизвестно" else f"Токен_{contract_address[-4:]}"
    await state.update_data(token_name=token_name)
    await message.answer(f"📝 Подтвердите имя токена: *{token_name}*. Всё верно?", parse_mode="Markdown", reply_markup=get_token_name_confirmation_keyboard())
    await state.set_state(TokenStates.waiting_for_name_confirmation)

async def confirm_token_name(callback: types.CallbackQuery, state: FSMContext):
    if should_log("interface"):
        logger.info(f"Callback 'confirm_token_name' получен от {callback.from_user.id}")
        logger.info("Подтверждение названия токена")
    data = await state.get_data()
    token_name = data["token_name"]
    contract_address = data["contract_address"]
    await state.set_state(TokenStates.waiting_for_thread_confirmation)
    await callback.message.edit_text(
        f"📝 Ветка для токена {token_name} ({contract_address[-4:]}) уже создана?\nЕсли да, скопируйте команду: ```/get_thread_id``` и вставьте её в нужную ветку.",
        reply_markup=get_thread_confirmation_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

async def reject_token_name(callback: types.CallbackQuery, state: FSMContext):
    if should_log("interface"):
        logger.info(f"Callback 'reject_token_name' получен от {callback.from_user.id}")
        logger.info("Отмена имени токена нажата")
    await callback.message.edit_text("📝 Введите адрес контракта токена (например, 0x...):", reply_markup=get_back_button())
    await state.set_state(TokenStates.waiting_for_contract_address)
    await callback.answer()

async def thread_exists(callback: types.CallbackQuery, state: FSMContext):
    if should_log("interface"):
        logger.info(f"Callback 'thread_exists' получен от {callback.from_user.id}")
        logger.info("Тред существует нажато")
    await callback.message.edit_text(
        "📝 Введите ID треда (например, 123456789):\n💡 Чтобы узнать ID ветки, отправьте команду ```/get_thread_id``` в нужной ветке.",
        reply_markup=get_back_button(),
        parse_mode="Markdown"
    )
    await state.set_state(TokenStates.waiting_for_thread_id)
    await callback.answer()

async def thread_not_exists(callback: types.CallbackQuery, state: FSMContext):
    if should_log("interface"):
        logger.info(f"Callback 'thread_not_exists' получен от {callback.from_user.id}")
        logger.info("Тред не существует нажато")
    user_data = await state.get_data()
    contract_address = user_data["contract_address"]
    token_name = user_data["token_name"]
    decimals = await get_token_info(contract_address)
    decimals = decimals["tokenDecimal"]
    db.tracked_tokens.add_tracked_token(contract_address, token_name, decimals=int(decimals) if decimals.isdigit() else 18)
    await state.set_state(TokenStates.waiting_for_add_to_all_final_confirmation)
    await callback.message.edit_text(
        f"💎 Токен {token_name} ({contract_address[-4:]}) добавлен успешно!\nДобавить токен ко всем отслеживаемым кошелькам?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да", callback_data="add_to_all_yes"), InlineKeyboardButton(text="❌ Нет", callback_data="add_to_all_no")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="home")]
        ]),
        parse_mode="Markdown"
    )
    await callback.answer()

async def process_thread_id(message: types.Message, state: FSMContext):
    if should_log("interface"):
        logger.info(f"Сообщение с ID треда от {message.from_user.id}: {message.text}")
        logger.info(f"Введен ID треда: {message.text}")
    thread_id = message.text.strip()
    if not thread_id.isdigit():
        await message.answer("❌ ID треда должен быть числом.", reply_markup=get_back_button())
        return
    user_data = await state.get_data()
    contract_address = user_data["contract_address"]
    token_name = user_data["token_name"]
    token_info = await get_token_info(contract_address)
    decimals = token_info["tokenDecimal"]
    db.tracked_tokens.add_tracked_token(contract_address, token_name, thread_id=thread_id, decimals=int(decimals) if decimals.isdigit() else 18)
    if should_log("interface"):
        logger.info(f"Токен добавлен: {token_name} ({contract_address})")
    await state.set_state(TokenStates.waiting_for_add_to_all_final_confirmation)
    await message.answer(
        f"💎 Токен {token_name} ({contract_address[-4:]}) добавлен успешно в тред {thread_id}!\nДобавить токен ко всем отслеживаемым кошелькам?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да", callback_data="add_to_all_yes"), InlineKeyboardButton(text="❌ Нет", callback_data="add_to_all_no")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="home")]
        ]),
        parse_mode="Markdown"
    )

async def add_to_all_yes(callback: types.CallbackQuery, state: FSMContext):
    if should_log("interface"):
        logger.info(f"Callback 'add_to_all_yes' получен от {callback.from_user.id}")
        logger.info("Добавление токена ко всем кошелькам подтверждено")
    data = await state.get_data()
    token_name = data.get("token_name")
    contract_address = data.get("contract_address")
    try:
        db.reconnect()
        wallets = db.wallets.get_all_wallets()
        if not wallets:
            logger.warning("Нет отслеживаемых кошельков для добавления токена")
            await callback.answer("⚠️ Нет отслеживаемых кошельков!", show_alert=True)
        else:
            for wallet in wallets:
                wallet_id = wallet[0]
                current_tokens = wallet[3].split(",") if wallet[3] else []
                if token_name and token_name not in current_tokens:
                    current_tokens.append(token_name)
                    db.wallets.update_wallet_tokens(wallet_id, ",".join(current_tokens))
                    if should_log("db"):
                        logger.info(f"Токен {token_name} добавлен к кошельку ID {wallet_id}")
            await callback.answer(f"✅ Токен {token_name} добавлен ко всем кошелькам!", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка при добавлении токена {token_name} ко всем кошелькам: {str(e)}", exc_info=True)
        await callback.answer("❌ Ошибка при добавлении токена ко всем кошелькам!", show_alert=True)
    await callback.message.edit_text(
        f"💎 Токен {token_name} ({contract_address[-4:] if contract_address else 'unknown'}) успешно настроен!",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )
    await state.clear()

async def add_to_all_no(callback: types.CallbackQuery, state: FSMContext):
    if should_log("interface"):
        logger.info(f"Callback 'add_to_all_no' получен от {callback.from_user.id}")
        logger.info("Добавление токена ко всем кошелькам отклонено")
    data = await state.get_data()
    token_name = data.get("token_name")
    contract_address = data.get("contract_address")
    await callback.message.edit_text(
        f"💎 Токен {token_name} ({contract_address[-4:] if contract_address else 'unknown'}) успешно настроен!",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )
    await state.clear()
    await callback.answer()

async def edit_token_start(callback: types.CallbackQuery, state: FSMContext):
    if should_log("interface"):
        logger.info(f"Callback 'edit_token' получен от {callback.from_user.id}: {callback.data}")
        logger.info(f"Редактирование токена: {callback.data}")
    token_id = callback.data.replace("edit_token_", "")
    try:
        token_id = int(token_id)
    except ValueError:
        if should_log("debug"):
            logger.debug(f"Некорректный token_id: {token_id}")
        await callback.answer("❌ Ошибка: неверный ID токена!", show_alert=True)
        return
    token = db.tracked_tokens.get_token_by_id(token_id)
    if not token:
        await callback.answer("❌ Токен не найден!", show_alert=True)
        return
    await callback.message.edit_text(
        f"📝 Текущий тред для токена {token[2]}: {token[3] or 'Не указан'}\n💡 Чтобы узнать ID треда, отправьте команду ```/get_thread_id``` в нужной ветке.",
        reply_markup=get_back_button(),
        parse_mode="Markdown"
    )
    await state.update_data(token_id=token_id)
    await state.set_state(TokenStates.waiting_for_edit_thread_id)
    await callback.answer()

async def edit_token_thread_new(callback: types.CallbackQuery, state: FSMContext):
    if should_log("interface"):
        logger.info(f"Callback 'edit_token_thread_new' получен от {callback.from_user.id}: {callback.data}")
        logger.info(f"Редактирование треда токена: {callback.data}")
    token_id = callback.data.replace("edit_token_thread_", "")
    try:
        token_id = int(token_id)
    except ValueError:
        if should_log("debug"):
            logger.debug(f"Некорректный token_id из callback_data: {token_id}")
        await callback.answer("❌ Ошибка: неверный ID токена!", show_alert=True)
        return
    db.reconnect()
    token = db.tracked_tokens.get_token_by_id(token_id)
    if not token:
        if should_log("debug"):
            logger.debug(f"Токен с ID {token_id} не найден в базе: {db.tracked_tokens.get_all_tracked_tokens()}")
        await callback.answer("❌ Токен не найден!", show_alert=True)
        return
    if should_log("debug"):
        logger.debug(f"Токен найден: ID={token[0]}, Имя={token[2]}, Текущий тред={token[3]}")
    await state.update_data(token_id=token_id)
    await callback.message.edit_text(
        f"📝 Текущий тред для токена {token[2]}: {token[3] or 'Не указан'}\n💡 Чтобы узнать ID треда, отправьте команду ```/get_thread_id``` в нужной ветке.",
        reply_markup=get_back_button(),
        parse_mode="Markdown"
    )
    await state.set_state(TokenStates.waiting_for_edit_thread_id)
    await callback.answer()

async def process_edit_thread_id(message: types.Message, state: FSMContext):
    if should_log("interface"):
        logger.info(f"Сообщение с новым ID треда токена от {message.from_user.id}: {message.text}")
        logger.info(f"Введен новый ID треда токена: {message.text}")
    thread_id = message.text.strip()
    if not thread_id.isdigit():
        await message.answer("❌ ID треда должен быть числом.", reply_markup=get_back_button())
        return
    user_data = await state.get_data()
    token_id = user_data["token_id"]
    token = db.tracked_tokens.get_token_by_id(token_id)
    if not token:
        await message.answer("❌ Токен не найден!", reply_markup=get_back_button())
        await state.clear()
        return
    new_thread_id = thread_id if thread_id.isdigit() else None
    db.tracked_tokens.update_token_thread(token_id, new_thread_id)
    token_name = token[2]
    await message.answer(
        f"💎 Тред для токена {token_name} обновлен на {new_thread_id or 'Не указан'}!",
        reply_markup=get_token_control_keyboard(token_id)
    )
    await state.clear()

async def delete_token(callback: types.CallbackQuery, state: FSMContext):
    if should_log("interface"):
        logger.info(f"Callback 'delete_token' получен от {callback.from_user.id}: {callback.data}")
        logger.info(f"Удаление токена: {callback.data}")
    token_id = callback.data.replace("delete_token_", "")
    try:
        token_id = int(token_id)
    except ValueError:
        if should_log("debug"):
            logger.debug(f"Некорректный token_id: {token_id}")
        await callback.answer("❌ Ошибка: неверный ID токена!", show_alert=True)
        return
    token = db.tracked_tokens.get_token_by_id(token_id)
    if not token:
        await callback.answer("❌ Токен не найден!", show_alert=True)
        return
    token_name = token[2]
    db.tracked_tokens.delete_tracked_token(token_id)
    db.reconnect()
    wallets = db.wallets.get_all_wallets()
    for wallet in wallets:
        wallet_id = wallet[0]
        current_tokens = wallet[3].split(",") if wallet[3] else []
        if token_name in current_tokens:
            current_tokens.remove(token_name)
            new_tokens = ",".join(current_tokens) if current_tokens else ""
            db.wallets.update_wallet_tokens(wallet_id, new_tokens)
            if should_log("db"):
                logger.info(f"Токен {token_name} удалён из кошелька ID {wallet_id}")
    text, reply_markup = get_tracked_tokens_list()
    await callback.message.edit_text(text, reply_markup=reply_markup, disable_web_page_preview=True)
    await callback.answer(f"🗑 Токен {token_name} удалён!")