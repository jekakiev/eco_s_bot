from aiogram import types
from aiogram.fsm.context import FSMContext
from .keyboards import (
    get_main_menu, get_back_button, get_tokens_keyboard, get_wallet_control_keyboard,
    get_wallets_list, get_tracked_tokens_list, get_token_control_keyboard,
    get_token_name_confirmation_keyboard, get_thread_confirmation_keyboard, get_commands_list,
    get_settings_list, get_interval_edit_keyboard, get_log_edit_keyboard
)
from .states import WalletStates, TokenStates, SettingStates
from database import Database
from logger_config import logger
import requests
from settings import ARBISCAN_API_KEY

db = Database()

# === ПОКАЗАТЬ КОШЕЛЬКИ ===
async def show_wallets(callback: types.CallbackQuery):
    logger.info("Кнопка 'Показать кошельки' нажата")
    try:
        text, reply_markup = get_wallets_list()
        await callback.message.answer(text, disable_web_page_preview=True, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Ошибка при отправке списка кошельков: {str(e)}")
        await callback.message.answer("❌ Произошла ошибка.", reply_markup=get_back_button())

# === ДОБАВИТЬ КОШЕЛЕК: НАЧАЛО ===
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
    await state.update_data(selected_tokens=[])
    await message.answer("🪙 Выберите монеты для отслеживания:", reply_markup=get_tokens_keyboard([], is_edit=False))

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
    is_edit = "wallet_id" in data
    await callback.message.edit_reply_markup(reply_markup=get_tokens_keyboard(selected_tokens, is_edit=is_edit))

# === ПОДТВЕРЖДЕНИЕ ВЫБОРА ТОКЕНОВ ПРИ ДОБАВЛЕНИИ ===
async def confirm_tokens(callback: types.CallbackQuery, state: FSMContext):
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

# === СОХРАНЕНИЕ ТОКЕНОВ ПРИ РЕДАКТИРОВАНИИ ===
async def save_tokens(callback: types.CallbackQuery, state: FSMContext):
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

# === УДАЛЕНИЕ КОШЕЛЬКА ===
async def delete_wallet(callback: types.CallbackQuery):
    wallet_id = callback.data.split("_")[2]
    db.remove_wallet(wallet_id)
    await callback.message.edit_text("🗑 Кошелек удалён!", reply_markup=get_main_menu())

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
    wallet = db.get_wallet_by_id(wallet_id)
    text = f"✅ Имя кошелька обновлено на: {new_name}\n_________\nИмя кошелька: {wallet['name']}\nАдрес кошелька: {wallet['address']}"
    await state.clear()
    await message.answer(text, reply_markup=get_wallet_control_keyboard(wallet_id))

# === ИЗМЕНЕНИЕ ТОКЕНОВ ===
async def edit_tokens_start(callback: types.CallbackQuery, state: FSMContext):
    wallet_id = callback.data.split("_")[2]
    wallet = db.get_wallet_by_id(wallet_id)
    current_tokens = wallet["tokens"].split(",") if wallet["tokens"] else []
    await state.update_data(wallet_id=wallet_id, selected_tokens=current_tokens)
    await callback.message.edit_text("🪙 Выберите монеты для отслеживания:", reply_markup=get_tokens_keyboard(current_tokens, is_edit=True))

# === ПОКАЗАТЬ ОТСЛЕЖИВАЕМЫЕ ТОКЕНЫ ===
async def show_tokens(callback: types.CallbackQuery):
    text, reply_markup = get_tracked_tokens_list()
    await callback.message.answer(text, disable_web_page_preview=True, reply_markup=reply_markup)

# === ДОБАВИТЬ ТОКЕН: НАЧАЛО ===
async def add_token_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(TokenStates.waiting_for_contract_address)
    await callback.message.edit_text("📝 Введите адрес контракта токена:", reply_markup=get_back_button())

# === ВВОД АДРЕСА ТОКЕНА ===
async def process_contract_address(message: types.Message, state: FSMContext):
    contract_address = message.text.lower()
    params = {
        "module": "account",
        "action": "tokentx",
        "contractaddress": contract_address,
        "startblock": 0,
        "endblock": 99999999,
        "sort": "desc",
        "apikey": ARBISCAN_API_KEY
    }
    response = requests.get("https://api.arbiscan.io/api", params=params)
    if response.status_code == 200 and response.json().get("status") == "1":
        token_info = response.json()["result"][0]
        token_name = token_info.get("tokenName", "Неизвестно")
        await state.update_data(contract_address=contract_address, token_name=token_name)
        await state.set_state(TokenStates.waiting_for_name_confirmation)
        await message.answer(f"🪙 Название токена: *{token_name}*. Всё верно?", parse_mode="Markdown", reply_markup=get_token_name_confirmation_keyboard())
    else:
        logger.error(f"Ошибка проверки токена {contract_address}: {response.status_code}, {response.text}")
        await message.answer("❌ Не удалось проверить токен. Проверьте адрес и попробуйте ещё раз.", reply_markup=get_back_button())

# === ПОДТВЕРЖДЕНИЕ НАЗВАНИЯ ТОКЕНА ===
async def confirm_token_name(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(TokenStates.waiting_for_thread_confirmation)
    await callback.message.edit_text("🧵 Создана ли уже ветка для этого токена?", reply_markup=get_thread_confirmation_keyboard())

async def reject_token_name(callback: types.CallbackQuery, state: FSMContext):
    text, reply_markup = get_tracked_tokens_list()
    await state.clear()
    await callback.message.edit_text(f"😂 Ой, промахнулся! Но не переживай, ты всё равно молодец.\n_________\n{text}", reply_markup=reply_markup)

# === ПОДТВЕРЖДЕНИЕ СУЩЕСТВОВАНИЯ ТРЕДА ===
async def thread_exists(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(TokenStates.waiting_for_thread_id)
    await callback.message.edit_text(
        "📌 Введите ID треда для сигналов:\n💡 Чтобы узнать ID ветки, отправьте команду `/get_thread_id` прямо в нужный тред.",
        parse_mode="Markdown",
        reply_markup=get_back_button()
    )

async def thread_not_exists(callback: types.CallbackQuery, state: FSMContext):
    text, reply_markup = get_tracked_tokens_list()
    await state.clear()
    await callback.message.edit_text(f"😅 Ветка не готова? Ничего страшного, создай её и возвращайся!\n_________\n{text}", reply_markup=reply_markup)

# === ВВОД ID ТРЕДА ===
async def process_thread_id(message: types.Message, state: FSMContext):
    try:
        thread_id = int(message.text)
        data = await state.get_data()
        db.add_tracked_token(data["token_name"], data["contract_address"], thread_id)
        logger.info(f"Добавлен токен: {data['token_name']} ({data['contract_address']}) с тредом {thread_id}")
        text, reply_markup = get_tracked_tokens_list()
        await state.clear()
        await message.answer(f"✅ Токен успешно добавлен!\n_________\n{text}", reply_markup=reply_markup)
    except ValueError:
        await message.answer("❌ ID треда должен быть числом. Попробуйте ещё раз:", reply_markup=get_back_button())
    except Exception as e:
        logger.error(f"Ошибка при добавлении токена: {str(e)}")
        await message.answer("❌ Произошла ошибка при добавлении токена.", reply_markup=get_back_button())

# === РЕДАКТИРОВАНИЕ ТОКЕНА ===
async def edit_token_start(callback: types.CallbackQuery, state: FSMContext):
    token_id = callback.data.split("_")[2]
    token = db.get_tracked_token_by_id(token_id)
    text = f"Токен: {token['token_name']}\nАдрес: {token['contract_address']}\nТекущий тред: {token['thread_id']}"
    await callback.message.edit_text(text, reply_markup=get_token_control_keyboard(token_id))

async def edit_token_thread(callback: types.CallbackQuery, state: FSMContext):
    token_id = callback.data.split("_")[2]
    await state.update_data(token_id=token_id)
    await state.set_state(TokenStates.waiting_for_edit_thread_id)
    await callback.message.edit_text(
        "📌 Введите новый ID треда:\n💡 Чтобы узнать ID ветки, отправьте команду `/get_thread_id` прямо в нужный тред.",
        parse_mode="Markdown",
        reply_markup=get_back_button()
    )

async def process_edit_thread_id(message: types.Message, state: FSMContext):
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

# === УДАЛЕНИЕ ТОКЕНА ===
async def delete_token(callback: types.CallbackQuery):
    token_id = callback.data.split("_")[2]
    db.remove_tracked_token(token_id)
    text, reply_markup = get_tracked_tokens_list()
    await callback.message.edit_text(f"🗑 Токен удалён!\n_________\n{text}", reply_markup=reply_markup)

# === ПОКАЗАТЬ КОМАНДЫ ===
async def show_commands(callback: types.CallbackQuery):
    text, reply_markup = get_commands_list()
    await callback.message.answer(text, parse_mode="Markdown", reply_markup=reply_markup)

# === ПОКАЗАТЬ НАСТРОЙКИ ===
async def show_settings(callback: types.CallbackQuery):
    logger.info("Кнопка 'Настройки' нажата")
    text, reply_markup = get_settings_list()
    await callback.message.answer(text, disable_web_page_preview=True, reply_markup=reply_markup)

# === РЕДАКТИРОВАНИЕ НАСТРОЙКИ ===
async def edit_setting_start(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Нажата кнопка настройки: {callback.data}")
    setting_name = callback.data.split("_")[2]
    current_value = db.get_setting(setting_name)
    if current_value is None:
        # Fallback если настройка не найдена
        default_values = {
            "CHECK_INTERVAL": "10",
            "LOG_TRANSACTIONS": "0",
            "LOG_SUCCESSFUL_TRANSACTIONS": "0"
        }
        current_value = default_values.get(setting_name, "0")
        logger.warning(f"Настройка {setting_name} не найдена в базе, использую значение по умолчанию: {current_value}")
        db.update_setting(setting_name, current_value)  # Сохраняем дефолтное значение в базу

    if setting_name == "CHECK_INTERVAL":
        text = f"⚙️ Интервал проверки\nТекущее значение: {current_value} секунд\nВведите интервал обновления в секундах (мин. 5):"
        await state.set_state(SettingStates.waiting_for_setting_value)
        await callback.message.edit_text(text, reply_markup=get_interval_edit_keyboard())
    else:  # LOG_TRANSACTIONS или LOG_SUCCESSFUL_TRANSACTIONS
        text = f"⚙️ {setting_name.replace('_', ' ').title()}\nТекущее значение: {'Вкл' if int(current_value) else 'Выкл'}"
        await callback.message.edit_text(text, reply_markup=get_log_edit_keyboard(setting_name))
    await state.update_data(setting_name=setting_name)

async def process_setting_value(message: types.Message, state: FSMContext):
    logger.info(f"Введено значение настройки: {message.text}")
    try:
        new_value = message.text
        data = await state.get_data()
        setting_name = data["setting_name"]
        
        if setting_name == "CHECK_INTERVAL":
            new_value = int(new_value)
            if new_value < 5:
                raise ValueError("Интервал должен быть не менее 5 секунд")
        
        db.update_setting(setting_name, str(new_value))
        text, reply_markup = get_settings_list()
        await state.clear()
        await message.answer(f"✅ Настройка {setting_name} обновлена на: {new_value}\n_________\n{text}", reply_markup=reply_markup)
    except ValueError as e:
        await message.answer(f"❌ Ошибка: {str(e)}. Попробуйте ещё раз:", reply_markup=get_interval_edit_keyboard())

# === УСТАНОВКА ЗНАЧЕНИЯ ЛОГОВ ===
async def set_log_value(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"Нажата кнопка вкл/выкл логов: {callback.data}")
    parts = callback.data.split("_")
    setting_name = parts[1]
    value = parts[2]
    db.update_setting(setting_name, value)
    text, reply_markup = get_settings_list()
    await callback.message.edit_text(f"✅ Настройка {setting_name} обновлена на: {'Вкл' if value == '1' else 'Выкл'}\n_________\n{text}", reply_markup=reply_markup)

# === ГЛАВНОЕ МЕНЮ ===
async def go_home(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🏠 Главное меню:", reply_markup=get_main_menu())