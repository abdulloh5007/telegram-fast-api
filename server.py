import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from api import routers
from api.client import ws_manager, client_manager

WEB_DIR = os.path.join(os.path.dirname(__file__), "web")


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await client_manager.disconnect_all()


app = FastAPI(title="Telegram Chat Viewer", lifespan=lifespan)

for router in routers:
    app.include_router(router)


@app.get("/")
async def index():
    path = os.path.join(WEB_DIR, "index.html")
    if os.path.exists(path):
        return FileResponse(path)
    return {"error": "Web UI not found"}


@app.get("/countries.json")
async def countries():
    path = os.path.join(WEB_DIR, "countries.json")
    if os.path.exists(path):
        return FileResponse(path, media_type="application/json")
    return []


@app.get("/favicon.ico")
async def favicon():
    path = os.path.join(WEB_DIR, "favicon.ico")
    if os.path.exists(path):
        return FileResponse(path, media_type="image/x-icon")
    return Response(status_code=204)


@app.get("/read")
async def read_backup():
    path = os.path.join(WEB_DIR, "read.html")
    if os.path.exists(path):
        return FileResponse(path)
    return {"error": "Reader not found"}


@app.get("/admin")
async def admin_panel():
    path = os.path.join(WEB_DIR, "admin.html")
    if os.path.exists(path):
        return FileResponse(path)
    return {"error": "Admin not found"}


@app.get("/login")
async def login_page():
    path = os.path.join(WEB_DIR, "login.html")
    if os.path.exists(path):
        return FileResponse(path)
    return {"error": "Login page not found"}


@app.websocket("/ws/{session_id}/{dialog_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, dialog_id: str):
    print(f"[WS] New connection: {session_id} / {dialog_id}")
    
    try:
        tc = await client_manager.get(session_id, enable_realtime=True)
    except Exception as e:
        print(f"[WS] Failed to get client: {e}")
        await websocket.close(code=4001)
        return
    
    print(f"[WS] Telethon client ready for {session_id}")
    
    key = f"{session_id}:{dialog_id}"
    await ws_manager.connect(key, websocket)
    print(f"[WS] Client connected to {key}")
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        print(f"[WS] Client disconnected from {key}")
    finally:
        ws_manager.disconnect(key, websocket)
        asyncio.create_task(client_manager.disconnect_if_unused(session_id))


if os.path.exists(WEB_DIR):
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
