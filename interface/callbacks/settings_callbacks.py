from aiogram import types
from aiogram.fsm.context import FSMContext
from ..keyboards import get_commands_list, get_settings_list, get_interval_edit_keyboard, get_main_menu
from ..states import SettingStates
from app_config import db  # Імпортуємо db з app_config
from utils.logger_config import logger, should_log, update_log_settings
import asyncio
from config.bot_instance import bot

async def show_commands(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Callback 'show_commands' получен от {callback.from_user.id}")
    if should_log("interface"):
        logger.info("Кнопка 'Показать команды' нажата")
    text, reply_markup = get_commands_list()
    await callback.message.answer(text, parse_mode="Markdown", reply_markup=reply_markup)
    await callback.answer()

async def show_settings(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Callback 'show_settings' получен от {callback.from_user.id}")
    if should_log("interface"):
        logger.info("Кнопка 'Настройки' нажата")
    check_interval = db.settings.get_setting("CHECK_INTERVAL", "150")
    send_last = "✅ВКЛ" if int(db.settings.get_setting("SEND_LAST_TRANSACTION", "0")) else "❌ВЫКЛ"
    api_errors = "✅ВКЛ" if int(db.settings.get_setting("API_ERRORS", "0")) else "❌ВЫКЛ"
    transaction_info = "✅ВКЛ" if int(db.settings.get_setting("TRANSACTION_INFO", "0")) else "❌ВЫКЛ"
    interface_info = "✅ВКЛ" if int(db.settings.get_setting("INTERFACE_INFO", "0")) else "❌ВЫКЛ"
    debug = "✅ВКЛ" if int(db.settings.get_setting("DEBUG", "0")) else "❌ВЫКЛ"
    text, reply_markup = get_settings_list(check_interval, send_last, api_errors, transaction_info, interface_info, debug)
    msg = await callback.message.edit_text(text, reply_markup=reply_markup, disable_web_page_preview=True)
    await state.update_data(settings_message_id=msg.message_id, check_interval=check_interval, send_last=send_last, api_errors=api_errors, transaction_info=transaction_info, interface_info=interface_info, debug=debug)
    await callback.answer()

async def edit_setting_start(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Callback 'edit_setting' получен от {callback.from_user.id}: {callback.data}")
    if should_log("interface"):
        logger.info(f"Нажата кнопка настройки: {callback.data}")
    setting_name = callback.data.replace("edit_setting_", "")
    data = await state.get_data()
    current_value = data.get("check_interval", db.settings.get_setting(setting_name, "150"))
    if setting_name == "CHECK_INTERVAL":
        text = f"⚙️ Интервал проверки\nТекущее значение: {current_value} секунд\nВведите интервал обновления в секундах (мин. 1):"
        msg = await callback.message.edit_text(text, reply_markup=get_interval_edit_keyboard())
        await state.update_data(settings_message_id=msg.message_id, setting_name=setting_name)
    await state.set_state(SettingStates.waiting_for_setting_value)  # Додано встановлення стану
    await callback.answer()

async def toggle_setting(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Callback 'toggle_setting' получен от {callback.from_user.id}: {callback.data}")
    if should_log("interface"):
        logger.info(f"Нажата кнопка переключения настройки: {callback.data}")
    setting_name = callback.data.replace("toggle_", "")
    data = await state.get_data()
    
    # Локальні значення для кнопок
    check_interval = data.get("check_interval", "150")
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
    db.settings.set_setting(setting_name, db_value)
    await asyncio.sleep(0.5)
    update_log_settings()
    
    # Оновлення клавіатури з локальними значеннями
    text, reply_markup = get_settings_list(check_interval, send_last, api_errors, transaction_info, interface_info, debug)
    try:
        await bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=data.get("settings_message_id"),
            text=text,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
        msg = await bot.send_message(chat_id=callback.message.chat.id, text="Тестовое сообщение для получения ID")  # Тест для оновлення ID
        await msg.delete()
    except Exception as e:
        logger.error(f"Ошибка редактирования сообщения: {str(e)}")
        msg = await callback.message.answer(text, reply_markup=reply_markup, disable_web_page_preview=True)
        await state.update_data(settings_message_id=msg.message_id, check_interval=check_interval, send_last=send_last, api_errors=api_errors, transaction_info=transaction_info, interface_info=interface_info, debug=debug)
    await state.update_data(check_interval=check_interval, send_last=send_last, api_errors=api_errors, transaction_info=transaction_info, interface_info=interface_info, debug=debug, settings_message_id=data.get("settings_message_id"))
    await callback.answer()

async def process_setting_value(message: types.Message, state: FSMContext):
    logger.info(f"Сообщение с новым значением настройки от {message.from_user.id}: {message.text}")
    if should_log("interface"):
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
        
        # Запис у базу
        db.settings.set_setting(setting_name, db_value)
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
        try:
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=data.get("settings_message_id"),
                text=text,
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
            msg = await bot.send_message(chat_id=message.chat.id, text="Тестовое сообщение для получения ID")  # Тест для оновлення ID
            await msg.delete()
        except Exception as e:
            logger.error(f"Ошибка редактирования сообщения: {str(e)}")
            msg = await message.answer(text, reply_markup=reply_markup, disable_web_page_preview=True)
            await state.update_data(settings_message_id=msg.message_id, check_interval=check_interval, send_last=data.get("send_last", "❌ВЫКЛ"), api_errors=data.get("api_errors", "❌ВЫКЛ"), transaction_info=data.get("transaction_info", "✅ВКЛ"), interface_info=data.get("interface_info", "❌ВЫКЛ"), debug=data.get("debug", "❌ВЫКЛ"))
        await state.update_data(check_interval=check_interval, settings_message_id=data.get("settings_message_id"))
        await state.clear()
    except ValueError as e:
        await message.answer(f"❌ Ошибка: {str(e)}. Попробуйте ещё раз:", reply_markup=get_interval_edit_keyboard())
    except Exception as e:
        if should_log("api_errors"):
            logger.error(f"Ошибка при обновлении настройки: {str(e)}")
        await message.answer("❌ Произошла ошибка при обновлении настройки.", reply_markup=get_main_menu())

async def go_home(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Callback 'go_home' получен от {callback.from_user.id}")
    if should_log("interface"):
        logger.info("Возврат в главное меню")
    await state.clear()
    await callback.message.edit_text("🏠 Главное меню:", reply_markup=get_main_menu())
    await callback.answer()