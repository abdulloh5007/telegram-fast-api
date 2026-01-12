from fastapi import APIRouter
from telethon.tl.types import User, Chat, Channel

from api.models import DialogInfo
from api.client import client_manager

router = APIRouter()


def get_type(entity) -> str:
    if isinstance(entity, User):
        return "user"
    if isinstance(entity, Chat):
        return "group"
    if isinstance(entity, Channel):
        return "channel" if entity.broadcast else "supergroup"
    return "unknown"


@router.get("/api/dialogs/{session_id}", response_model=list[DialogInfo])
async def get_dialogs(session_id: str, limit: int = 50):
    c = await client_manager.get(session_id)
    result = []
    
    async for d in c.iter_dialogs(limit=limit):
        msg = None
        date = None
        
        if d.message:
            msg = d.message.text or ("[Media]" if d.message.media else None)
            if msg and len(msg) > 50:
                msg = msg[:50] + "..."
            date = d.message.date.isoformat() if d.message.date else None
        
        has_photo = hasattr(d.entity, 'photo') and d.entity.photo is not None
        
        result.append(DialogInfo(
            id=d.id,
            name=d.name or "Unknown",
            type=get_type(d.entity),
            unread_count=d.unread_count,
            last_message=msg,
            last_date=date,
            has_photo=has_photo
        ))
    
    return result
