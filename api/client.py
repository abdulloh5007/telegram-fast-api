import os
import asyncio
from typing import Optional
from fastapi import WebSocket, HTTPException
from telethon import TelegramClient, events
from telethon.tl.types import User, MessageMediaPhoto

from config import API_ID, API_HASH, SESSIONS_DIR


class ConnectionManager:
    def __init__(self):
        self.connections: dict[str, list[WebSocket]] = {}
    
    async def connect(self, key: str, ws: WebSocket):
        await ws.accept()
        self.connections.setdefault(key, []).append(ws)
    
    def disconnect(self, key: str, ws: WebSocket):
        if key in self.connections:
            self.connections[key] = [c for c in self.connections[key] if c != ws]
    
    async def broadcast(self, key: str, data: dict):
        dead = []
        for ws in self.connections.get(key, []):
            try:
                await ws.send_json(data)
            except:
                dead.append(ws)
        for ws in dead:
            self.disconnect(key, ws)
    
    def has_connections(self, session_id: str) -> bool:
        return any(k.startswith(f"{session_id}:") for k in self.connections if self.connections[k])


class ClientManager:
    def __init__(self, ws_manager: Optional[ConnectionManager] = None):
        self.clients: dict[str, TelegramClient] = {}
        self.locks: dict[str, asyncio.Lock] = {}
        self.ws_manager = ws_manager
        self.realtime_enabled: dict[str, bool] = {}
    
    async def get(self, session_id: str, enable_realtime: bool = False) -> TelegramClient:
        if session_id not in self.locks:
            self.locks[session_id] = asyncio.Lock()
        
        async with self.locks[session_id]:
            if session_id in self.clients and self.clients[session_id].is_connected():
                if enable_realtime and not self.realtime_enabled.get(session_id):
                    self._register_handlers(self.clients[session_id], session_id)
                    self.realtime_enabled[session_id] = True
                return self.clients[session_id]
            
            if session_id in self.clients:
                del self.clients[session_id]
            
            path = os.path.join(SESSIONS_DIR, session_id)
            if not os.path.exists(path + ".session"):
                raise HTTPException(404, "Session not found")
            
            for attempt in range(3):
                try:
                    client = TelegramClient(path, API_ID, API_HASH)
                    await client.connect()
                    
                    if not await client.is_user_authorized():
                        await client.disconnect()
                        raise HTTPException(401, "Not authorized")
                    
                    self.clients[session_id] = client
                    
                    if enable_realtime and self.ws_manager:
                        self._register_handlers(client, session_id)
                        self.realtime_enabled[session_id] = True
                        asyncio.create_task(self._run_client(client))
                    
                    return client
                except HTTPException:
                    raise
                except Exception as e:
                    if attempt == 2:
                        raise HTTPException(500, str(e))
                    await asyncio.sleep(0.5)
    
    async def _run_client(self, client: TelegramClient):
        try:
            await client.catch_up()
            while client.is_connected():
                await asyncio.sleep(1)
        except:
            pass
    
    def _register_handlers(self, client: TelegramClient, session_id: str):
        if not self.ws_manager:
            return
            
        @client.on(events.NewMessage)
        async def on_new_message(event):
            msg = event.message
            dialog_id = event.chat_id
            
            sender_name = None
            if msg.sender:
                if isinstance(msg.sender, User):
                    sender_name = msg.sender.first_name or ""
                    if msg.sender.last_name:
                        sender_name += f" {msg.sender.last_name}"
                elif hasattr(msg.sender, 'title'):
                    sender_name = msg.sender.title
            
            me = await client.get_me()
            
            media_type = None
            if msg.media:
                if isinstance(msg.media, MessageMediaPhoto):
                    media_type = "photo"
                else:
                    media_type = type(msg.media).__name__.replace("MessageMedia", "").lower()
            
            data = {
                "type": "new_message",
                "message": {
                    "id": msg.id,
                    "text": msg.text,
                    "date": msg.date.isoformat() if msg.date else "",
                    "sender_id": msg.sender_id,
                    "sender_name": sender_name,
                    "is_outgoing": msg.sender_id == me.id if msg.sender_id else False,
                    "has_media": msg.media is not None,
                    "media_type": media_type
                }
            }
            
            key = f"{session_id}:{dialog_id}"
            await self.ws_manager.broadcast(key, data)
    
    async def disconnect_if_unused(self, session_id: str):
        await asyncio.sleep(5)
        if self.ws_manager and not self.ws_manager.has_connections(session_id):
            self.realtime_enabled[session_id] = False
    
    async def disconnect_all(self):
        for client in self.clients.values():
            try:
                await client.disconnect()
            except:
                pass


ws_manager = ConnectionManager()
client_manager = ClientManager(ws_manager)
