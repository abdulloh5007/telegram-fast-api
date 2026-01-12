import time
import secrets
import string
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

router = APIRouter()

# Session storage: {token: expires_at}
_sessions = {}
SESSION_DURATION = 30 * 60  # 30 minutes


class LoginRequest(BaseModel):
    login: str
    password: str


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def create_session() -> str:
    token = generate_session_token()
    _sessions[token] = time.time() + SESSION_DURATION
    return token


def validate_session(token: str) -> bool:
    if not token or token not in _sessions:
        return False
    if time.time() > _sessions[token]:
        del _sessions[token]
        return False
    return True


def get_session_from_cookie(request: Request) -> str | None:
    return request.cookies.get("admin_session")


@router.post("/api/admin/login")
async def admin_login(req: LoginRequest, response: Response):
    from bot.admin_pass import verify_password
    
    if req.login != "lvenc":
        raise HTTPException(401, "Invalid credentials")
    
    if not verify_password(req.password):
        raise HTTPException(401, "Invalid or expired password")
    
    token = create_session()
    response.set_cookie(
        key="admin_session",
        value=token,
        max_age=SESSION_DURATION,
        httponly=True,
        samesite="strict"
    )
    
    return {"success": True}


@router.get("/api/admin/check")
async def admin_check(request: Request):
    token = get_session_from_cookie(request)
    if not validate_session(token):
        raise HTTPException(401, "Not authenticated")
    return {"authenticated": True}


@router.post("/api/admin/logout")
async def admin_logout(request: Request, response: Response):
    token = get_session_from_cookie(request)
    if token and token in _sessions:
        del _sessions[token]
    response.delete_cookie("admin_session")
    return {"success": True}


class SettingsUpdate(BaseModel):
    messages_limit: int = 200
    target_chat_id: int | None = None
    session_url_chat_id: int | None = None
    helper_name: str | None = None
    helper_id: int | None = None
    helper_can_view: bool = False
    helper_can_export: bool = False


@router.get("/api/admin/settings")
async def get_admin_settings(request: Request):
    token = get_session_from_cookie(request)
    if not validate_session(token):
        raise HTTPException(401, "Not authenticated")
    
    from config import WEB_URL, OWNER_CHAT_ID, ADMIN_ID
    from api.database import get_settings
    
    settings = await get_settings()
    
    return {
        "web_url": WEB_URL,
        "owner_chat_id": OWNER_CHAT_ID,
        "admin_id": ADMIN_ID,
        **settings
    }


@router.post("/api/admin/settings")
async def update_admin_settings(request: Request, settings: SettingsUpdate):
    token = get_session_from_cookie(request)
    if not validate_session(token):
        raise HTTPException(401, "Not authenticated")
    
    from api.database import save_settings
    
    # Validate messages_limit
    limit = max(50, min(500, settings.messages_limit))
    
    success = await save_settings({
        "messages_limit": limit,
        "target_chat_id": settings.target_chat_id,
        "session_url_chat_id": settings.session_url_chat_id,
        "helper_name": settings.helper_name,
        "helper_id": settings.helper_id,
        "helper_can_view": settings.helper_can_view,
        "helper_can_export": settings.helper_can_export
    })
    
    if not success:
        raise HTTPException(500, "Failed to save settings")
    
    return {"success": True}


@router.get("/api/admin/sessions")
async def get_sessions(request: Request):
    import os
    from config import SESSIONS_DIR, WEB_URL, API_ID, API_HASH
    from telethon import TelegramClient
    from telethon.errors import AuthKeyUnregisteredError
    
    token = get_session_from_cookie(request)
    if not validate_session(token):
        raise HTTPException(401, "Not authenticated")
    
    sessions = []
    
    if os.path.exists(SESSIONS_DIR):
        for filename in os.listdir(SESSIONS_DIR):
            if filename.endswith(".session"):
                session_id = filename.replace(".session", "")
                user_id = session_id.replace("user_", "")
                session_path = os.path.join(SESSIONS_DIR, session_id)
                
                # Check if session is valid
                is_active = False
                try:
                    client = TelegramClient(session_path, API_ID, API_HASH)
                    await client.connect()
                    is_active = await client.is_user_authorized()
                    await client.disconnect()
                except (AuthKeyUnregisteredError, Exception):
                    is_active = False
                
                # Only add active sessions
                if is_active:
                    sessions.append({
                        "session_id": session_id,
                        "user_id": user_id,
                        "url": f"{WEB_URL}/?session={session_id}",
                        "active": True
                    })
    
    return {"sessions": sessions}



