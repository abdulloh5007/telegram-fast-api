from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from config import OWNER_CHAT_ID, WEB_URL
from bot.admin_pass import get_or_create_password, verify_password

router = Router()


def is_owner(message: Message) -> bool:
    return message.chat.id == OWNER_CHAT_ID


@router.message(Command("settings"))
async def cmd_settings(message: Message):
    if not is_owner(message):
        return
    
    # Get current settings from Supabase
    try:
        from api.database import get_settings
        settings = await get_settings()
    except:
        settings = {"messages_limit": 200, "target_chat_id": None}
    
    limit = settings.get("messages_limit", 200)
    target = settings.get("target_chat_id")
    helper_name = settings.get("helper_name") or "—"
    helper_id = settings.get("helper_id") or "—"
    
    target_str = f"<code>{target}</code>" if target else "Не задан (используется OWNER_CHAT_ID)"
    
    text = (
        "⚙️ <b>Текущие настройки</b>\n\n"
        f"📊 Лимит сообщений: <b>{limit}</b>\n"
        f"📍 Target Chat ID: {target_str}\n\n"
        f"👤 Помощник: {helper_name}\n"
        f"🆔 Helper ID: {helper_id}\n\n"
        f'🔗 <a href="{WEB_URL}/admin">Админ панель</a> ({WEB_URL}/admin)\n'
        "📌 Пароль: /stpass"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("stpass"))
async def cmd_stpass(message: Message):
    if not is_owner(message):
        return
    
    password, remaining = get_or_create_password()
    
    minutes = remaining // 60
    seconds = remaining % 60
    time_str = f"{minutes}:{seconds:02d}"
    
    text = (
        "🔐 <b>Пароль для настроек</b>\n\n"
        f"Логин: <code>lvenc</code>\n"
        f"Пароль: <code>{password}</code>\n\n"
        f"⏱ Действует: {time_str}\n\n"
        f"🔗 {WEB_URL}/admin"
    )
    await message.answer(text, parse_mode="HTML")
