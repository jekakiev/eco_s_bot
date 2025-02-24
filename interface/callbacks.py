from aiogram import types
from aiogram.fsm.context import FSMContext
from .keyboards import (
    get_main_menu, get_back_button, get_tokens_keyboard, get_wallet_control_keyboard,
    get_wallets_list, get_tracked_tokens_list, get_token_control_keyboard,
    get_token_name_confirmation_keyboard, get_thread_confirmation_keyboard, get_commands_list,
    get_settings_list, get_interval_edit_keyboard
)
from .states import WalletStates, TokenStates, SettingStates
from database import Database
from utils.logger_config import logger, update_log_settings
import aiohttp
import time
import asyncio
from config.settings import ARBISCAN_API_KEY
from config.bot_instance import bot

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

async def show_tokens(callback: types.CallbackQuery):
    logger.info(f"Callback 'show_tokens' получен от {callback.from_user.id}")
    if int(db.get_setting("INTERFACE_INFO") or 0):
        logger.info("Кнопка 'Показать токены' нажата")
    text, reply_markup = get_tracked_tokens_list()
    await callback.message.answer(text, disable_web_page_preview=True, reply_markup=reply_markup)
    await callback.answer()

async def add_token_start(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Callback 'add_token' получен от {callback.from_user.id}")
    if int(db.get_setting("INTERFACE_INFO") or 0):
        logger.info("Кнопка 'Добавить токен' нажата")
    await state.set_state(TokenStates.waiting_for_contract_address)
    await callback.message.edit_text("📝 Введите адрес контракта токена:", reply_markup=get_back_button())
    await callback.answer()

async def process_contract_address(message: types.Message, state: FSMContext):
    logger.info(f"Сообщение с адресом контракта от {message.from_user.id}: {message.text}")
    if int(db.get_setting("INTERFACE_INFO") or 0):
        logger.info(f"Введен адрес контракта токена: {message.text}")
    contract_address = message.text.lower()
    params = {
        "module": "account",
        "action": "tokentx",
        "contractaddress": contract_address,
        "startblock": 0,
        "endblock": 99999999,
        "sort": "desc",
        "offset": 0,
        "limit": 10,
        "apikey": ARBISCAN_API_KEY
    }
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.arbiscan.io/api", params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("status") == "1":
                    token_info = data["result"][0]
                    token_name = token_info.get("tokenName", "Неизвестно")
                    await state.update_data(contract_address=contract_address, token_name=token_name)
                    await state.set_state(TokenStates.waiting_for_name_confirmation)
                    await message.answer(f"🪙 Название токена: *{token_name}*. Всё верно?", parse_mode="Markdown", reply_markup=get_token_name_confirmation_keyboard())
                else:
                    if int(db.get_setting("API_ERRORS") or 1):
                        logger.error(f"Ошибка проверки токена {contract_address}: {data.get('message', 'Нет данных')}")
                    await message.answer("❌ Не удалось проверить токен. Проверьте адрес и попробуйте ещё раз.", reply_markup=get_back_button())
            else:
                if int(db.get_setting("API_ERRORS") or 1):
                    logger.error(f"Ошибка проверки токена {contract_address}: HTTP {response.status}")
                await message.answer("❌ Не удалось проверить токен. Проверьте адрес и попробуйте ещё раз.", reply_markup=get_back_button())

async def confirm_token_name(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Callback 'confirm_token_name' получен от {callback.from_user.id}")
    if int(db.get_setting("INTERFACE_INFO") or 0):
        logger.info("Подтверждение названия токена")
    await state.set_state(TokenStates.waiting_for_thread_confirmation)
    await callback.message.edit_text("🧵 Создана ли уже ветка для этого токена?", reply_markup=get_thread_confirmation_keyboard())
    await callback.answer()

async def reject_token_name(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Callback 'reject_token_name' получен от {callback.from_user.id}")
    if int(db.get_setting("INTERFACE_INFO") or 0):
        logger.info("Отклонение названия токена")
    text, reply_markup = get_tracked_tokens_list()
    await state.clear()
    await callback.message.edit_text(f"😂 Ой, промахнулся! Но не переживай, ты всё равно молодец.\n_________\n{text}", reply_markup=reply_markup)
    await callback.answer()

async def thread_exists(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Callback 'thread_exists' получен от {callback.from_user.id}")
    if int(db.get_setting("INTERFACE_INFO") or 0):
        logger.info("Подтверждение существования треда")
    await state.set_state(TokenStates.waiting_for_thread_id)
    await callback.message.edit_text(
        "📌 Введите ID треда для сигналов:\n💡 Чтобы узнать ID ветки, отправьте команду `/get_thread_id` прямо в нужный тред.",
        parse_mode="Markdown",
        reply_markup=get_back_button()
    )
    await callback.answer()

async def thread_not_exists(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Callback 'thread_not_exists' получен от {callback.from_user.id}")
    if int(db.get_setting("INTERFACE_INFO") or 0):
        logger.info("Указание, что тред не существует")
    text, reply_markup = get_tracked_tokens_list()
    await state.clear()
    await callback.message.edit_text(f"😅 Ветка не готова? Ничего страшного, создай её и возвращайся!\n_________\n{text}", reply_markup=reply_markup)
    await callback.answer()

async def process_thread_id(message: types.Message, state: FSMContext):
    logger.info(f"Сообщение с ID треда от {message.from_user.id}: {message.text}")
    if int(db.get_setting("INTERFACE_INFO") or 0):
        logger.info(f"Введен ID треда: {message.text}")
    try:
        thread_id = int(message.text)
        data = await state.get_data()
        db.add_tracked_token(data["token_name"], data["contract_address"], thread_id)
        if int(db.get_setting("INTERFACE_INFO") or 0):
            logger.info(f"Добавлен токен: {data['token_name']} ({data['contract_address']}) с тредом {thread_id}")
        text, reply_markup = get_tracked_tokens_list()
        await state.clear()
        await message.answer(f"✅ Токен успешно добавлен!\n_________\n{text}", reply_markup=reply_markup)
    except ValueError:
        await message.answer("❌ ID треда должен быть числом. Попробуйте ещё раз:", reply_markup=get_back_button())
    except Exception as e:
        if int(db.get_setting("API_ERRORS") or 1):
            logger.error(f"Ошибка при добавлении токена: {str(e)}")
        await message.answer("❌ Произошла ошибка при добавлении токена.", reply_markup=get_back_button())

async def edit_token_start(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Callback 'edit_token' получен от {callback.from_user.id}")
    token_id = callback.data.split("_")[2]
    if int(db.get_setting("INTERFACE_INFO") or 0):
        logger.info(f"Начало редактирования токена с ID {token_id}")
    token = db.get_tracked_token_by_id(token_id)
    text = f"Токен: {token['token_name']}\nАдрес: {token['contract_address']}\nТекущий тред: {token['thread_id']}"
    await callback.message.edit_text(text, reply_markup=get_token_control_keyboard(token_id))
    await callback.answer()

async def edit_token_thread(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Callback 'edit_token_thread' получен от {callback.from_user.id}")
    token_id = callback.data.split("_")[2]
    if int(db.get_setting("INTERFACE_INFO") or 0):
        logger.info(f"Начало изменения треда для токена с ID {token_id}")
    await state.update_data(token_id=token_id)
    await state.set_state(TokenStates.waiting_for_edit_thread_id)
    await callback.message.edit_text(
        "📌 Введите новый ID треда:\n💡 Чтобы узнать ID ветки, отправьте команду `/get_thread_id` прямо в нужный тред.",
        parse_mode="Markdown",
        reply_markup=get_back_button()
    )
    await callback.answer()

async def process_edit_thread_id(message: types.Message, state: FSMContext):
    logger.info(f"Сообщение с новым ID треда от {message.from_user.id}: {message.text}")
    if int(db.get_setting("INTERFACE_INFO") or 0):
        logger.info(f"Введен новый ID треда: {message.text}")
    try:
        thread_id = int(message.text)
        data = await state.get_data()
        token_id = data["token_id"]
        token = db.get_tracked_token_by_id(token_id)
        db.update_tracked_token(token_id, token["token_name"], thread_id)
        text = f"✅ Тред обновлён!\n_________\nТокен: {token['token_name']}\nАдрес: {token['contract_address']}\nТекущий тред: {token['thread_id']}"
        await state.clear()
        await message.answer(text, reply_markup=get_token_control_keyboard(token_id))
    except ValueError:
        await message.answer("❌ ID треда должен быть числом. Попробуйте ещё раз:", reply_markup=get_back_button())
    except Exception as e:
        if int(db.get_setting("API_ERRORS") or 1):
            logger.error(f"Ошибка при обновлении треда: {str(e)}")
        await message.answer("❌ Произошла ошибка при обновлении треда.", reply_markup=get_back_button())

async def delete_token(callback: types.CallbackQuery):
    logger.info(f"Callback 'delete_token' получен от {callback.from_user.id}")
    token_id = callback.data.split("_")[2]
    if int(db.get_setting("INTERFACE_INFO") or 0):
        logger.info(f"Удаление токена с ID {token_id}")
    db.remove_tracked_token(token_id)
    text, reply_markup = get_tracked_tokens_list()
    await callback.message.edit_text(f"🗑 Токен удалён!\n_________\n{text}", reply_markup=reply_markup)
    await callback.answer()

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
    msg = await callback.message.edit_text(text, reply_markup=reply_markup, disable_web_page_preview=True)
    await state.update_data(settings_message_id=msg.message_id)
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
    updated_value = "включено" if new_value == "1" else "выключено"
    new_text = f"✅ Настройка обновлена: {setting_name} теперь {updated_value}\n_____________________\n{text}"
    data = await state.get_data()
    settings_message_id = data.get("settings_message_id")
    try:
        await bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=settings_message_id,
            text=new_text,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Ошибка редактирования сообщения: {str(e)}")
        msg = await callback.message.answer(new_text, reply_markup=reply_markup, disable_web_page_preview=True)
        await state.update_data(settings_message_id=msg.message_id)
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
        updated_value = db.get_setting(setting_name)
        text, reply_markup = get_settings_list()
        settings_message_id = data.get("settings_message_id")
        try:
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=settings_message_id,
                text=f"✅ Настройка обновлена: {setting_name} теперь {updated_value} сек\n_____________________\n{text}",
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.error(f"Ошибка редактирования сообщения: {str(e)}")
            msg = await message.answer(f"✅ Настройка обновлена: {setting_name} теперь {updated_value} сек\n_____________________\n{text}",
                                       reply_markup=reply_markup, disable_web_page_preview=True)
            await state.update_data(settings_message_id=msg.message_id)
        await state.clear()
    except ValueError as e:
        await message.answer(f"❌ Ошибка: {str(e)}. Попробуйте ещё раз:", reply_markup=get_interval_edit_keyboard())
    except Exception as e:
        if int(db.get_setting("API_ERRORS") or 1):
            logger.error(f"Ошибка при обновлении настройки: {str(e)}")
        await message.answer("❌ Произошла ошибка при обновлении настройки.", reply_markup=get_back_button())

async def go_home(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Callback 'go_home' получен от {callback.from_user.id}")
    if int(db.get_setting("INTERFACE_INFO") or 0):
        logger.info("Возврат в главное меню")
    await state.clear()
    await callback.message.edit_text("🏠 Главное меню:", reply_markup=get_main_menu())
    await callback.answer()