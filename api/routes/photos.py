from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from api.client import client_manager

router = APIRouter()


@router.get("/api/photo/{session_id}/user/{user_id}")
async def user_photo(session_id: str, user_id: int):
    c = await client_manager.get(session_id)
    
    try:
        entity = await c.get_entity(user_id)
        if hasattr(entity, 'photo') and entity.photo:
            data = await c.download_profile_photo(entity, file=bytes)
            if data:
                return Response(content=data, media_type="image/jpeg")
    except:
        pass
    
    raise HTTPException(404, "Photo not found")


@router.get("/api/photo/{session_id}/dialog/{dialog_id}")
async def dialog_photo(session_id: str, dialog_id: int):
    c = await client_manager.get(session_id)
    
    try:
        entity = await c.get_entity(dialog_id)
        if hasattr(entity, 'photo') and entity.photo:
            data = await c.download_profile_photo(entity, file=bytes)
            if data:
                return Response(content=data, media_type="image/jpeg")
    except:
        pass
    
    raise HTTPException(404, "Photo not found")


@router.get("/api/media/{session_id}/{dialog_id}/{message_id}")
async def message_media(session_id: str, dialog_id: int, message_id: int):
    c = await client_manager.get(session_id)
    
    try:
        msg = await c.get_messages(dialog_id, ids=message_id)
        if msg and msg.media:
            data = await c.download_media(msg, file=bytes)
            if data:
                return Response(content=data, media_type="image/jpeg")
    except:
        pass
    
    raise HTTPException(404, "Media not found")
