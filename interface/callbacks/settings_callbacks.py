# /interface/callbacks/settings_callbacks.py
from aiogram import types
from aiogram.fsm.context import FSMContext
from ..keyboards import get_main_menu, get_settings_list, get_interval_edit_keyboard, get_commands_list
from ..states import SettingStates
from app_config import db
from utils.logger_config import logger, should_log, update_log_settings
import asyncio
from config.bot_instance import bot

async def show_commands(callback: types.CallbackQuery, state: FSMContext):
    if should_log("interface"):
        logger.info(f"Callback 'show_commands' получен от {callback.from_user.id}")
        logger.info("Кнопка 'Показать команды' нажата")
    text, reply_markup = get_commands_list()
    await callback.message.answer(text, parse_mode="Markdown", reply_markup=reply_markup)
    await callback.answer()

async def show_settings(callback: types.CallbackQuery, state: FSMContext):
    if should_log("interface"):
        logger.info(f"Callback 'show_settings' получен от {callback.from_user.id}")
        logger.info("Кнопка 'Настройки' нажата")
    check_interval = db.settings.get_setting("CHECK_INTERVAL", "150")
    api_errors = "✅ВКЛ" if int(db.settings.get_setting("API_ERRORS", "0")) else "❌ВЫКЛ"
    transaction_info = "✅ВКЛ" if int(db.settings.get_setting("TRANSACTION_INFO", "0")) else "❌ВЫКЛ"
    interface_info = "✅ВКЛ" if int(db.settings.get_setting("INTERFACE_INFO", "0")) else "❌ВЫКЛ"
    debug = "✅ВКЛ" if int(db.settings.get_setting("DEBUG", "0")) else "❌ВЫКЛ"
    db_info = "✅ВКЛ" if int(db.settings.get_setting("DB_INFO", "0")) else "❌ВЫКЛ"
    min_other_token_value = db.settings.get_setting("MIN_OTHER_TOKEN_VALUE", "50")  # Новая настройка
    text, reply_markup = get_settings_list(check_interval, api_errors, transaction_info, interface_info, debug, db_info, min_other_token_value)
    msg = await callback.message.edit_text(text, reply_markup=reply_markup, disable_web_page_preview=True)
    await state.update_data(settings_message_id=msg.message_id, check_interval=check_interval, api_errors=api_errors, transaction_info=transaction_info, interface_info=interface_info, debug=debug, db_info=db_info, min_other_token_value=min_other_token_value)
    await callback.answer()

async def edit_setting_start(callback: types.CallbackQuery, state: FSMContext):
    if should_log("interface"):
        logger.info(f"Callback 'edit_setting' получен от {callback.from_user.id}: {callback.data}")
        logger.info(f"Нажата кнопка настройки: {callback.data}")
    setting_name = callback.data.replace("edit_setting_", "")
    data = await state.get_data()
    current_value = data.get("check_interval", db.settings.get_setting(setting_name, "150"))
    if setting_name == "CHECK_INTERVAL":
        text = f"⚙️ Интервал проверки\nТекущее значение: {current_value} секунд\nВведите интервал обновления в секундах (мин. 1):"
        msg = await callback.message.edit_text(text, reply_markup=get_interval_edit_keyboard())
        await state.update_data(settings_message_id=msg.message_id, setting_name=setting_name)
    elif setting_name == "MIN_OTHER_TOKEN_VALUE":
        text = f"⚙️ Минимальная сумма для других токенов\nТекущее значение: ${current_value} USD\nВведите новую сумму в USD (мин. 1):"
        msg = await callback.message.edit_text(text, reply_markup=get_interval_edit_keyboard())
        await state.update_data(settings_message_id=msg.message_id, setting_name=setting_name)
    await state.set_state(SettingStates.waiting_for_setting_value)
    await callback.answer()

async def toggle_setting(callback: types.CallbackQuery, state: FSMContext):
    if should_log("interface"):
        logger.info(f"Callback 'toggle_setting' получен от {callback.from_user.id}: {callback.data}")
        logger.info(f"Нажата кнопка переключения настройки: {callback.data}")
    setting_name = callback.data.replace("toggle_", "")
    data = await state.get_data()
    
    check_interval = data.get("check_interval", "150")
    api_errors = data.get("api_errors", "❌ВЫКЛ")
    transaction_info = data.get("transaction_info", "✅ВКЛ")
    interface_info = data.get("interface_info", "❌ВЫКЛ")
    debug = data.get("debug", "❌ВЫКЛ")
    db_info = data.get("db_info", "❌ВЫКЛ")
    min_other_token_value = data.get("min_other_token_value", "50")
    
    if setting_name == "API_ERRORS":
        api_errors = "✅ВКЛ" if api_errors == "❌ВЫКЛ" else "❌ВЫКЛ"
        db_value = "1" if api_errors == "✅ВКЛ" else "0"
    elif setting_name == "TRANSACTION_INFO":
        transaction_info = "✅ВКЛ" if transaction_info == "❌ВЫКЛ" else "❌ВЫКЛ"
        db_value = "1" if transaction_info == "✅ВКЛ" else "0"
    elif setting_name == "INTERFACE_INFO":
        interface_info = "✅ВКЛ" if interface_info == "❌ВЫКЛ" else "❌ВЫКЛ"
        db_value = "1" if interface_info == "✅ВКЛ" else "0"
    elif setting_name == "DEBUG":
        debug = "✅ВКЛ" if debug == "❌ВЫКЛ" else "❌ВЫКЛ"
        db_value = "1" if debug == "✅ВКЛ" else "0"
    elif setting_name == "DB_INFO":
        db_info = "✅ВКЛ" if db_info == "❌ВЫКЛ" else "❌ВЫКЛ"
        db_value = "1" if db_info == "✅ВКЛ" else "0"
    
    db.settings.set_setting(setting_name, db_value)
    await asyncio.sleep(0.5)
    update_log_settings(db)
    
    text, reply_markup = get_settings_list(check_interval, api_errors, transaction_info, interface_info, debug, db_info, min_other_token_value)
    try:
        await bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=data.get("settings_message_id"),
            text=text,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
    except Exception as e:
        if should_log("api_errors"):
            logger.error(f"Ошибка редактирования сообщения: {str(e)}")
        msg = await callback.message.answer(text, reply_markup=reply_markup, disable_web_page_preview=True)
        await state.update_data(settings_message_id=msg.message_id, check_interval=check_interval, api_errors=api_errors, transaction_info=transaction_info, interface_info=interface_info, debug=debug, db_info=db_info, min_other_token_value=min_other_token_value)
    await state.update_data(check_interval=check_interval, api_errors=api_errors, transaction_info=transaction_info, interface_info=interface_info, debug=debug, db_info=db_info, min_other_token_value=min_other_token_value)
    await callback.answer()

async def process_setting_value(message: types.Message, state: FSMContext):
    if should_log("interface"):
        logger.info(f"Сообщение с новым значением настройки от {message.from_user.id}: {message.text}")
        logger.info(f"Введено значение настройки: {message.text}")
    try:
        new_value = message.text
        data = await state.get_data()
        setting_name = data["setting_name"]
        
        if setting_name == "CHECK_INTERVAL":
            new_value = int(new_value)
            if new_value < 1:
                raise ValueError("Интервал должен быть не менее 1 секунды")
            check_interval = f"{new_value} сек"
            db_value = str(new_value)
        elif setting_name == "MIN_OTHER_TOKEN_VALUE":
            new_value = float(new_value)
            if new_value < 1:
                raise ValueError("Минимальная сумма должна быть не менее 1 USD")
            check_interval = None  # Не используется для этой настройки
            db_value = str(new_value)
        
        db.settings.set_setting(setting_name, db_value)
        await asyncio.sleep(0.5)
        
        text, reply_markup = get_settings_list(
            check_interval=data.get("check_interval", "150"),
            api_errors=data.get("api_errors", "❌ВЫКЛ"),
            transaction_info=data.get("transaction_info", "✅ВКЛ"),
            interface_info=data.get("interface_info", "❌ВЫКЛ"),
            debug=data.get("debug", "❌ВЫКЛ"),
            db_info=data.get("db_info", "❌ВЫКЛ"),
            min_other_token_value=db.settings.get_setting("MIN_OTHER_TOKEN_VALUE", "50")
        )
        try:
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=data.get("settings_message_id"),
                text=text,
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
        except Exception as e:
            if should_log("api_errors"):
                logger.error(f"Ошибка редактирования сообщения: {str(e)}")
            msg = await message.answer(text, reply_markup=reply_markup, disable_web_page_preview=True)
            await state.update_data(settings_message_id=msg.message_id, check_interval=data.get("check_interval", "150"), api_errors=data.get("api_errors", "❌ВЫКЛ"), transaction_info=data.get("transaction_info", "✅ВКЛ"), interface_info=data.get("interface_info", "❌ВЫКЛ"), debug=data.get("debug", "❌ВЫКЛ"), db_info=data.get("db_info", "❌ВЫКЛ"), min_other_token_value=db.settings.get_setting("MIN_OTHER_TOKEN_VALUE", "50"))
        await state.update_data(check_interval=data.get("check_interval", "150"), min_other_token_value=db.settings.get_setting("MIN_OTHER_TOKEN_VALUE", "50"))
        await state.clear()
    except ValueError as e:
        await message.answer(f"❌ Ошибка: {str(e)}. Попробуйте ещё раз:", reply_markup=get_interval_edit_keyboard())
    except Exception as e:
        if should_log("api_errors"):
            logger.error(f"Ошибка при обновлении настройки: {str(e)}")
        await message.answer("❌ Произошла ошибка при обновлении настройки.", reply_markup=get_main_menu())

async def go_home(callback: types.CallbackQuery, state: FSMContext):
    if should_log("interface"):
        logger.info(f"Callback 'go_home' получен от {callback.from_user.id}")
        logger.info("Возврат в главное меню")
    await state.clear()
    await callback.message.edit_text("🏠 Главное меню:", reply_markup=get_main_menu())
    await callback.answer()