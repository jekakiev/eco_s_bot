from aiogram import types
from aiogram.fsm.context import FSMContext
from ..keyboards import get_tracked_tokens_list, get_back_button, get_token_control_keyboard, get_token_name_confirmation_keyboard, get_thread_confirmation_keyboard, get_main_menu
from ..states import TokenStates
from database import Database
from utils.logger_config import logger
import aiohttp
from config.settings import ARBISCAN_API_KEY

db = Database()

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