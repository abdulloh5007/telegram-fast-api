import os
import glob
from fastapi import APIRouter

from config import SESSIONS_DIR
from api.models import SessionInfo

router = APIRouter()


@router.get("/api/sessions", response_model=list[SessionInfo])
async def list_sessions():
    sessions = []
    for f in glob.glob(os.path.join(SESSIONS_DIR, "*.session")):
        sid = os.path.basename(f).replace(".session", "")
        sessions.append(SessionInfo(id=sid, name=sid.replace("user_", "User ")))
    return sessions
