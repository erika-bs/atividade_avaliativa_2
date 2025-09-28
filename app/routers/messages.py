from fastapi import APIRouter, Query, HTTPException
from bson import ObjectId
from datetime import datetime, timezone

from app.db import db, serialize
from app.models import MessageIn,MessageOut

router = APIRouter(prefix="/rooms", tags=["messages"])

# --- REST ---
@router.get("/{room}/messages")
async def get_messages(
    room: str, 
    limit: int = Query(20, ge=1, le=100), 
    before_id: str | None = Query(None)
):
    query = {"room": room}
    if before_id:
        try:
            query["_id"] = {"$lt": ObjectId(before_id)}
        except Exception:
            raise HTTPException(status_code=400,detail="before_id inválido")

    cursor = db()["messages"].find(query).sort("_id", -1).limit(limit)
    docs = [serialize(d) async for d in cursor]
    docs.reverse()
    next_cursor = docs[0]["_id"] if docs else None
    return {"items": docs, "next_cursor": next_cursor}


@router.post("/{room}/messages", status_code=201, response_model=MessageOut)
async def post_message(room:str,payload:MessageIn):
    username = payload.username[:50]
    content = payload.content.strip()

    if not content:
        raise HTTPException(status_code=400, detail="Mensagem vazia não é permitida.")

    doc = {
        "room": room,
        "username": username,
        "content": content[:1000],
        "created_at": datetime.now(timezone.utc),
    }
    res = await db()["messages"].insert_one(doc)
    doc["_id"] = res.inserted_id
    return serialize(doc)