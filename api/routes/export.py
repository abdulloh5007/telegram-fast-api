from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from telethon.tl.types import User, Chat, Channel
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import os
import json
import base64
from typing import Optional

from api.client import client_manager

router = APIRouter()


class ExportRequest(BaseModel):
    dialog_ids: Optional[list[int]] = None
    messages_limit: int = 50
    password: str


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


@router.post("/api/export/{session_id}")
async def export_data(session_id: str, req: ExportRequest):
    if not req.password or len(req.password) < 4:
        raise HTTPException(400, "Password must be at least 4 characters")
    
    try:
        c = await client_manager.get(session_id)
    except:
        raise HTTPException(404, "Session not found or expired")
    
    me = await c.get_me()
    
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
    
    limit = min(max(req.messages_limit, 10), 200)
    
    async for d in c.iter_dialogs(limit=100):
        if req.dialog_ids and d.id not in req.dialog_ids:
            continue
        
        dialog_data = {
            "id": d.id,
            "name": d.name or "Unknown",
            "type": get_type(d.entity),
            "messages": []
        }
        
        async for msg in c.iter_messages(d.id, limit=limit):
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
    
    encrypted = encrypt_data(data, req.password)
    
    return Response(
        content=encrypted,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="telegram_backup_{me.id}.enc"'
        }
    )


@router.post("/api/decrypt")
async def decrypt_file(password: str, file_content: str):
    try:
        raw = base64.b64decode(file_content)
        
        salt = raw[:16]
        nonce = raw[16:28]
        encrypted = raw[28:]
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = kdf.derive(password.encode('utf-8'))
        
        aesgcm = AESGCM(key)
        decrypted = aesgcm.decrypt(nonce, encrypted, None)
        
        return json.loads(decrypted.decode('utf-8'))
    except Exception as e:
        raise HTTPException(400, f"Decryption failed: {str(e)}")
