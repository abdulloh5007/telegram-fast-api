from fastapi import APIRouter

from api.models import UserInfo
from api.client import client_manager

router = APIRouter()


@router.get("/api/user/{session_id}", response_model=UserInfo)
async def get_user(session_id: str):
    c = await client_manager.get(session_id)
    me = await c.get_me()
    
    return UserInfo(
        id=me.id,
        first_name=me.first_name or "",
        last_name=me.last_name,
        username=me.username,
        phone=me.phone,
        has_photo=me.photo is not None
    )
