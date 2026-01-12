from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from telethon.tl.types import User, Chat, Channel
import asyncio
from typing import Optional

from api.client import client_manager
from api import database

router = APIRouter()


class BackupRequest(BaseModel):
    dialog_ids: Optional[list[int]] = None
    messages_limit: int = 50


def get_type(entity) -> str:
    if isinstance(entity, User):
        return "user"
    if isinstance(entity, Chat):
        return "group"
    if isinstance(entity, Channel):
        return "channel" if entity.broadcast else "supergroup"
    return "unknown"


@router.get("/api/backup/status/{session_id}")
async def backup_status(session_id: str):
    try:
        c = await client_manager.get(session_id)
        me = await c.get_me()
        has_existing = await database.has_backup(me.id)
        return {
            "configured": database.is_configured(),
            "has_backup": has_existing,
            "telegram_id": me.id
        }
    except:
        return {"configured": database.is_configured(), "has_backup": False}


@router.post("/api/backup/{session_id}")
async def backup_data(session_id: str, req: BackupRequest = BackupRequest()):
    if not database.is_configured():
        raise HTTPException(400, "Supabase not configured")
    
    try:
        c = await client_manager.get(session_id)
    except:
        raise HTTPException(404, "Session not found or expired")
    
    me = await c.get_me()
    
    if await database.has_backup(me.id):
        raise HTTPException(409, "Backup already exists. Delete old data first.")
    
    user_id = await database.save_user(
        telegram_id=me.id,
        first_name=me.first_name or "",
        last_name=me.last_name,
        username=me.username,
        phone=me.phone
    )
    
    if not user_id:
        raise HTTPException(500, "Failed to save user")
    
    dialogs_count = 0
    messages_count = 0
    limit = min(max(req.messages_limit, 10), 200)
    
    async for d in c.iter_dialogs(limit=100):
        if req.dialog_ids and d.id not in req.dialog_ids:
            continue
            
        dialog_id = await database.save_dialog(
            user_id=user_id,
            telegram_dialog_id=d.id,
            name=d.name or "Unknown",
            dialog_type=get_type(d.entity)
        )
        
        if dialog_id:
            dialogs_count += 1
            
            msgs = []
            async for msg in c.iter_messages(d.id, limit=limit):
                sender_name = None
                if msg.sender:
                    if isinstance(msg.sender, User):
                        sender_name = msg.sender.first_name or ""
                        if msg.sender.last_name:
                            sender_name += f" {msg.sender.last_name}"
                    elif hasattr(msg.sender, 'title'):
                        sender_name = msg.sender.title
                
                msgs.append({
                    "telegram_message_id": msg.id,
                    "text": msg.text,
                    "sender_name": sender_name,
                    "is_outgoing": msg.sender_id == me.id if msg.sender_id else False,
                    "date": msg.date.isoformat() if msg.date else None,
                    "has_media": msg.media is not None,
                    "media_type": type(msg.media).__name__ if msg.media else None
                })
            
            saved = await database.save_messages(dialog_id, msgs)
            messages_count += saved
        
        await asyncio.sleep(0.1)
    
    return {
        "success": True,
        "dialogs": dialogs_count,
        "messages": messages_count
    }


@router.delete("/api/backup/{telegram_id}")
async def delete_backup(telegram_id: int):
    if not database.is_configured():
        raise HTTPException(400, "Supabase not configured")
    
    result = await database.delete_user_data(telegram_id)
    return {"success": result}


@router.get("/api/saved/{telegram_id}")
async def get_saved_data(telegram_id: int):
    if not database.is_configured():
        raise HTTPException(400, "Supabase not configured")
    
    user = await database.get_saved_user(telegram_id)
    if not user:
        raise HTTPException(404, "No saved data found")
    
    dialogs = await database.get_saved_dialogs(user["id"])
    
    return {
        "user": user,
        "dialogs": dialogs
    }


@router.get("/api/saved/{telegram_id}/messages/{dialog_id}")
async def get_saved_messages(telegram_id: int, dialog_id: str):
    if not database.is_configured():
        raise HTTPException(400, "Supabase not configured")
    
    messages = await database.get_saved_messages(dialog_id)
    return {"messages": messages}
