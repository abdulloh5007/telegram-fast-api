import os
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from config import SESSIONS_DIR, WEB_URL
from bot.states import AuthStates
from bot import storage

router = Router()


def session_exists(user_id: int) -> bool:
    return os.path.exists(os.path.join(SESSIONS_DIR, f"user_{user_id}.session"))


def get_link(user_id: int) -> str:
    return f"{WEB_URL}?session=user_{user_id}"


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from telethon import TelegramClient
    from config import API_ID, API_HASH, SESSIONS_DIR
    import os
    
    user_id = message.from_user.id
    await state.clear()
    
    client = storage.get_client(user_id)
    if client:
        try:
            await client.disconnect()
        except:
            pass
        storage.remove_client(user_id)
    storage.remove_auth(user_id)
    
    # Check if session exists AND is active
    if session_exists(user_id):
        session_path = os.path.join(SESSIONS_DIR, f"user_{user_id}")
        try:
            check_client = TelegramClient(session_path, API_ID, API_HASH)
            await check_client.connect()
            is_active = await check_client.is_user_authorized()
            await check_client.disconnect()
            
            if is_active:
                await message.answer(
                    f"✅ У вас уже есть активная сессия!\n\n"
                    f"🔗 <b>Ваша ссылка:</b>\n<code>{get_link(user_id)}</code>\n\n"
                    f"Отправьте /newlogin для входа в другой аккаунт.",
                    parse_mode="HTML"
                )
                return
        except:
            pass
    
    # Show buttons for new users or inactive sessions
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Войти через бота", callback_data="continue_bot")]
    ])
    
    await message.answer(
        "👋 Привет!\n\n"
        f"🌐 Веб-логин: {WEB_URL}/login\n\n"
        "Или нажмите кнопку ниже:",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@router.callback_query(lambda c: c.data == "continue_bot")
async def callback_continue_bot(callback, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text(
        "📱 Отправьте номер телефона:\n<code>+79001234567</code>",
        parse_mode="HTML"
    )
    await state.set_state(AuthStates.waiting_phone)


@router.message(Command("mylink"))
async def cmd_mylink(message: Message):
    user_id = message.from_user.id
    
    if session_exists(user_id):
        await message.answer(
            f"🔗 <b>Ваша ссылка:</b>\n<code>{get_link(user_id)}</code>",
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Нет сессии. Отправьте /start")


@router.message(Command("newlogin"))
async def cmd_newlogin(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await state.clear()
    
    client = storage.get_client(user_id)
    if client:
        try:
            await client.disconnect()
        except:
            pass
        storage.remove_client(user_id)
    storage.remove_auth(user_id)
    
    await message.answer(
        "📱 Отправьте номер телефона:\n<code>+79001234567</code>",
        parse_mode="HTML"
    )
    await state.set_state(AuthStates.waiting_phone)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await state.clear()
    
    client = storage.get_client(user_id)
    if client:
        try:
            await client.disconnect()
        except:
            pass
        storage.remove_client(user_id)
    storage.remove_auth(user_id)
    
    await message.answer("❌ Отменено. /start")


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📋 <b>Команды:</b>\n\n"
        "/start - Начать\n"
        "/mylink - Ссылка на клиент\n"
        "/newlogin - Новый вход\n"
        "/chid - ID этого чата\n"
        "/cancel - Отмена",
        parse_mode="HTML"
    )


@router.message(Command("chid"))
async def cmd_chid(message: Message):
    await message.answer(
        f"📍 <b>Chat ID:</b>\n<code>{message.chat.id}</code>",
        parse_mode="HTML"
    )

