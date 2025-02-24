from aiogram import types
from aiogram.fsm.context import FSMContext
from ..keyboards import get_commands_list, get_settings_list, get_interval_edit_keyboard, get_main_menu
from ..states import SettingStates
from database import Database
from utils.logger_config import logger, update_log_settings
import asyncio
from config.bot_instance import bot

db = Database()

async def show_commands(callback: types.CallbackQuery):
    logger.info(f"Callback 'show_commands' получен от {callback.from_user.id}")
    if int(db.get_setting("INTERFACE_INFO") or 0):
        logger.info("Кнопка 'Показать команды' нажата")
    text, reply_markup = get_commands_list()
    await callback.message.answer(text, parse_mode="Markdown", reply_markup=reply_markup)
    await callback.answer()

async def show_settings(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Callback 'show_settings' получен от {callback.from_user.id}")
    if int(db.get_setting("INTERFACE_INFO") or 0):
        logger.info("Кнопка 'Настройки' нажата")
    settings = db.get_all_settings()
    check_interval = settings.get("CHECK_INTERVAL", "10")
    send_last = "✅ВКЛ" if settings.get("SEND_LAST_TRANSACTION", "0") == "1" else "❌ВЫКЛ"
    api_errors = "✅ВКЛ" if settings.get("API_ERRORS", "1") == "1" else "❌ВЫКЛ"
    transaction_info = "✅ВКЛ" if settings.get("TRANSACTION_INFO", "0") == "1" else "❌ВЫКЛ"
    interface_info = "✅ВКЛ" if settings.get("INTERFACE_INFO", "0") == "1" else "❌ВЫКЛ"
    debug = "✅ВКЛ" if settings.get("DEBUG", "0") == "1" else "❌ВЫКЛ"
    text, reply_markup = get_settings_list(check_interval, send_last, api_errors, transaction_info, interface_info, debug)
    msg = await callback.message.edit_text(text, reply_markup=reply_markup, disable_web_page_preview=True)
    await state.update_data(settings_message_id=msg.message_id, check_interval=check_interval, send_last=send_last, api_errors=api_errors, transaction_info=transaction_info, interface_info=interface_info, debug=debug)
    await callback.answer()

async def edit_setting_start(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Callback 'edit_setting' получен от {callback.from_user.id}: {callback.data}")
    if int(db.get_setting("INTERFACE_INFO") or 0):
        logger.info(f"Нажата кнопка настройки: {callback.data}")
    setting_name = callback.data.replace("edit_setting_", "")
    data = await state.get_data()
    current_value = data.get("check_interval", db.get_setting(setting_name) or "10")
    if setting_name == "CHECK_INTERVAL":
        text = f"⚙️ Интервал проверки\nТекущее значение: {current_value} секунд\nВведите интервал обновления в секундах (мин. 1):"
        await state.set_state(SettingStates.waiting_for_setting_value)
        await callback.message.edit_text(text, reply_markup=get_interval_edit_keyboard())
    await state.update_data(setting_name=setting_name)
    await callback.answer()

async def toggle_setting(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Callback 'toggle_setting' получен от {callback.from_user.id}: {callback.data}")
    if int(db.get_setting("INTERFACE_INFO") or 0):
        logger.info(f"Нажата кнопка переключения настройки: {callback.data}")
    setting_name = callback.data.replace("toggle_", "")
    data = await state.get_data()
    
    # Локальні значення для кнопок
    send_last = data.get("send_last", "❌ВЫКЛ")
    api_errors = data.get("api_errors", "❌ВЫКЛ")
    transaction_info = data.get("transaction_info", "✅ВКЛ")
    interface_info = data.get("interface_info", "❌ВЫКЛ")
    debug = data.get("debug", "❌ВЫКЛ")
    
    # Зміна стану локально
    if setting_name == "SEND_LAST_TRANSACTION":
        send_last = "✅ВКЛ" if send_last == "❌ВЫКЛ" else "❌ВЫКЛ"
        db_value = "1" if send_last == "✅ВКЛ" else "0"
    elif setting_name == "API_ERRORS":
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
    
    # Запис у базу
    db.update_setting(setting_name, db_value)
    await asyncio.sleep(0.5)
    update_log_settings()
    
    # Оновлення клавіатури з локальними значеннями
    text, reply_markup = get_settings_list(
        check_interval=data.get("check_interval", "150"),
        send_last=send_last,
        api_errors=api_errors,
        transaction_info=transaction_info,
        interface_info=interface_info,
        debug=debug
    )
    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=data.get("settings_message_id"),
        text=text,
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )
    await state.update_data(send_last=send_last, api_errors=api_errors, transaction_info=transaction_info, interface_info=interface_info, debug=debug)
    await callback.answer()

async def process_setting_value(message: types.Message, state: FSMContext):
    logger.info(f"Сообщение с новым значением настройки от {message.from_user.id}: {message.text}")
    if int(db.get_setting("INTERFACE_INFO") or 0):
        logger.info(f"Введено значение настройки: {message.text}")
    try:
        new_value = message.text
        data = await state.get_data()
        setting_name = data["setting_name"]
        
        if setting_name == "CHECK_INTERVAL":
            new_value = int(new_value)
            if new_value < 1:
                raise ValueError("Интервал должен быть не менее 1 секунды")
            db_value = str(new_value)
            check_interval = f"{new_value} сек"
        
        # Запис у базу
        db.update_setting(setting_name, db_value)
        await asyncio.sleep(0.5)
        
        # Оновлення клавіатури з локальними значеннями
        text, reply_markup = get_settings_list(
            check_interval=check_interval,
            send_last=data.get("send_last", "❌ВЫКЛ"),
            api_errors=data.get("api_errors", "❌ВЫКЛ"),
            transaction_info=data.get("transaction_info", "✅ВКЛ"),
            interface_info=data.get("interface_info", "❌ВЫКЛ"),
            debug=data.get("debug", "❌ВЫКЛ")
        )
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=data.get("settings_message_id"),
            text=text,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
        await state.update_data(check_interval=check_interval)
        await state.clear()
    except ValueError as e:
        await message.answer(f"❌ Ошибка: {str(e)}. Попробуйте ещё раз:", reply_markup=get_interval_edit_keyboard())
    except Exception as e:
        if int(db.get_setting("API_ERRORS") or 1):
            logger.error(f"Ошибка при обновлении настройки: {str(e)}")
        await message.answer("❌ Произошла ошибка при обновлении настройки.", reply_markup=get_main_menu())

async def go_home(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Callback 'go_home' получен от {callback.from_user.id}")
    if int(db.get_setting("INTERFACE_INFO") or 0):
        logger.info("Возврат в главное меню")
    await state.clear()
    await callback.message.edit_text("🏠 Главное меню:", reply_markup=get_main_menu())
    await callback.answer()