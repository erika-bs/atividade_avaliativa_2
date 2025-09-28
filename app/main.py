from __future__ import annotations
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from datetime import datetime, timezone

from app.db import db, serialize
from app.ws_manager import WSManager
from app.routers import messages
from app.models import MessageIn

app = FastAPI(title="FastAPI Chat + MongoDB Atlas (fix datetime)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Static client ---
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", include_in_schema=False)
async def index():
    return FileResponse("app/static/index.html")

# inclui as rotas REST recortadas para routers/messages.py
app.include_router(messages.router)

# --- WS ---
manager = WSManager()

@app.websocket("/ws/{room}")
async def ws_room(ws: WebSocket, room: str):
    await manager.connect(room, ws)
    try:
        # histórico inicial
        cursor = db()["messages"].find({"room": room}).sort("_id", -1).limit(20)
        items = [serialize(d) async for d in cursor]
        items.reverse()
        await ws.send_json({"type": "history", "items": items})

        while True:
            payload = await ws.receive_json()
            try:
                data = MessageIn(**payload) 
                username = data.username[:50]
                content = data.content.strip()
                if not content:
                    await ws.send_json({"type": "error", "detail": "Mensagem vazia não é permitida."})
                    continue
            except ValidationError as e:
                await ws.send_json({"type": "error", "detail": "Dados inválidos", "errors": e.errors()})
                continue

            doc = {
                "room": room,
                "username": username,
                "content": content[:1000],
                "created_at": datetime.now(timezone.utc),
            }
            res = await db()["messages"].insert_one(doc)
            doc["_id"] = res.inserted_id
            await manager.broadcast(room, {"type": "message", "item": serialize(doc)})

    except WebSocketDisconnect:
        pass
    except Exception:
        await ws.close()
    finally:
        manager.disconnect(room, ws)
