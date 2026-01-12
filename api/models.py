from typing import Optional
from pydantic import BaseModel


class SessionInfo(BaseModel):
    id: str
    name: str


class UserInfo(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    phone: Optional[str] = None
    has_photo: bool = False


class DialogInfo(BaseModel):
    id: int
    name: str
    type: str
    unread_count: int = 0
    last_message: Optional[str] = None
    last_date: Optional[str] = None
    has_photo: bool = False


class MessageInfo(BaseModel):
    id: int
    text: Optional[str] = None
    date: str
    sender_id: Optional[int] = None
    sender_name: Optional[str] = None
    is_outgoing: bool = False
    has_media: bool = False
    media_type: Optional[str] = None
    entities: Optional[list[dict]] = None

