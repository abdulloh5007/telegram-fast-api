from fastapi import APIRouter
from telethon.tl.types import User, MessageMediaPhoto, MessageEntityBold, MessageEntityItalic, MessageEntityCode, MessageEntityPre, MessageEntityStrike, MessageEntityUnderline, MessageEntityTextUrl, MessageEntityUrl, MessageEntityMention, MessageEntityHashtag

from api.models import MessageInfo
from api.client import client_manager

router = APIRouter()


def get_name(entity) -> str:
    if isinstance(entity, User):
        name = entity.first_name or ""
        if entity.last_name:
            name += f" {entity.last_name}"
        return name.strip() or "Unknown"
    if hasattr(entity, 'title'):
        return entity.title
    return "Unknown"


def extract_entities(entities) -> list:
    if not entities:
        return []
    
    result = []
    for e in entities:
        entity_type = None
        extra = {}
        
        if isinstance(e, MessageEntityBold):
            entity_type = "bold"
        elif isinstance(e, MessageEntityItalic):
            entity_type = "italic"
        elif isinstance(e, MessageEntityCode):
            entity_type = "code"
        elif isinstance(e, MessageEntityPre):
            entity_type = "pre"
        elif isinstance(e, MessageEntityStrike):
            entity_type = "strike"
        elif isinstance(e, MessageEntityUnderline):
            entity_type = "underline"
        elif isinstance(e, MessageEntityTextUrl):
            entity_type = "text_url"
            extra["url"] = e.url
        elif isinstance(e, MessageEntityUrl):
            entity_type = "url"
        elif isinstance(e, MessageEntityMention):
            entity_type = "mention"
        elif isinstance(e, MessageEntityHashtag):
            entity_type = "hashtag"
        
        if entity_type:
            result.append({
                "type": entity_type,
                "offset": e.offset,
                "length": e.length,
                **extra
            })
    
    return result


@router.get("/api/messages/{session_id}/{dialog_id}", response_model=list[MessageInfo])
async def get_messages(session_id: str, dialog_id: int, limit: int = 50):
    c = await client_manager.get(session_id)
    me = await c.get_me()
    result = []
    
    async for msg in c.iter_messages(dialog_id, limit=limit):
        sender_id = None
        sender_name = None
        
        if msg.sender:
            sender_id = msg.sender_id
            sender_name = get_name(msg.sender)
        
        media_type = None
        if msg.media:
            if isinstance(msg.media, MessageMediaPhoto):
                media_type = "photo"
            else:
                media_type = type(msg.media).__name__.replace("MessageMedia", "").lower()
        
        result.append(MessageInfo(
            id=msg.id,
            text=msg.text,
            date=msg.date.isoformat() if msg.date else "",
            sender_id=sender_id,
            sender_name=sender_name,
            is_outgoing=msg.sender_id == me.id if msg.sender_id else False,
            has_media=msg.media is not None,
            media_type=media_type,
            entities=extract_entities(msg.entities)
        ))
    
    result.reverse()
    return result

