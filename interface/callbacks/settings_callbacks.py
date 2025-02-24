from aiogram import types
from aiogram.fsm.context import FSMContext
from ..keyboards import get_commands_list, get_settings_list, get_interval_edit_keyboard, get_main_menu
from ..states import SettingStates
from database import Database
from utils.logger_config import logger, update_log_settings
import asyncio

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
    text, reply_markup = get_settings_list()
    await callback.message.edit_text(text, reply_markup=reply_markup, disable_web_page_preview=True)
    await callback.answer()

async def edit_setting_start(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Callback 'edit_setting' получен от {callback.from_user.id}: {callback.data}")
    if int(db.get_setting("INTERFACE_INFO") or 0):
        logger.info(f"Нажата кнопка настройки: {callback.data}")
    setting_name = callback.data.replace("edit_setting_", "")
    current_value = db.get_setting(setting_name)
    if current_value is None:
        default_values = {
            "CHECK_INTERVAL": "10",
            "SEND_LAST_TRANSACTION": "0",
            "API_ERRORS": "1",
            "TRANSACTION_INFO": "0",
            "INTERFACE_INFO": "0",
            "DEBUG": "0"
        }
        current_value = default_values.get(setting_name, "0")
        if int(db.get_setting("API_ERRORS") or 1):
            logger.warning(f"Настройка {setting_name} не найдена в базе, использую значение по умолчанию: {current_value}")
        db.update_setting(setting_name, current_value)

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
    current_value = db.get_setting(setting_name)
    if current_value is None:
        current_value = "0"
        db.update_setting(setting_name, current_value)
        if int(db.get_setting("API_ERRORS") or 1):
            logger.warning(f"Настройка {setting_name} не найдена в базе, установлено значение по умолчанию: {current_value}")
    
    new_value = "1" if int(current_value) == 0 else "0"
    db.update_setting(setting_name, new_value)
    await asyncio.sleep(0.5)
    update_log_settings()
    text, reply_markup = get_settings_list()
    await callback.message.edit_text(text, reply_markup=reply_markup, disable_web_page_preview=True)
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
        
        db.update_setting(setting_name, str(new_value))
        await asyncio.sleep(0.5)
        text, reply_markup = get_settings_list()
        await message.answer(text, reply_markup=reply_markup, disable_web_page_preview=True)
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