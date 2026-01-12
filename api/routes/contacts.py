"""Contacts API - Export and Broadcast"""
import os
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Optional

from telethon import TelegramClient
from telethon.tl.functions.contacts import GetContactsRequest
from telethon.tl.types import InputPeerUser

from config import API_ID, API_HASH, SESSIONS_DIR

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


async def get_client(session: str) -> TelegramClient:
    """Get connected Telegram client for session"""
    session_path = os.path.join(SESSIONS_DIR, session)
    if not os.path.exists(f"{session_path}.session"):
        raise HTTPException(404, "Session not found")
    
    client = TelegramClient(session_path, API_ID, API_HASH)
    await client.connect()
    
    if not await client.is_user_authorized():
        await client.disconnect()
        raise HTTPException(401, "Session not authorized")
    
    return client


@router.get("/{session}")
async def get_contacts(session: str):
    """Get all contacts for a session"""
    client = await get_client(session)
    
    try:
        result = await client(GetContactsRequest(hash=0))
        
        contacts = []
        for user in result.users:
            contacts.append({
                "id": user.id,
                "first_name": user.first_name or "",
                "last_name": user.last_name or "",
                "username": user.username,
                "phone": user.phone,
                "access_hash": user.access_hash
            })
        
        return {"contacts": contacts, "count": len(contacts)}
    
    finally:
        await client.disconnect()


@router.post("/{session}/broadcast")
async def broadcast_message(
    session: str,
    text: str = Form(...),
    file: Optional[UploadFile] = File(None),
    delete_for_me: bool = Form(True)
):
    """Send message to all contacts"""
    client = await get_client(session)
    
    try:
        # Get contacts
        result = await client(GetContactsRequest(hash=0))
        
        if not result.users:
            raise HTTPException(400, "No contacts found")
        
        # Prepare file if uploaded
        file_path = None
        if file:
            file_path = f"/tmp/{file.filename}"
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
        
        sent_count = 0
        errors = []
        
        for user in result.users:
            try:
                peer = InputPeerUser(user.id, user.access_hash)
                
                if file_path:
                    msg = await client.send_file(peer, file_path, caption=text)
                else:
                    msg = await client.send_message(peer, text)
                
                # Delete for me only
                if delete_for_me and msg:
                    await client.delete_messages(peer, [msg.id], revoke=False)
                
                sent_count += 1
                
            except Exception as e:
                errors.append(f"{user.first_name}: {str(e)}")
        
        # Clean up file
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        
        return {
            "success": True,
            "sent": sent_count,
            "total": len(result.users),
            "errors": errors[:5]  # First 5 errors only
        }
    
    finally:
        await client.disconnect()
