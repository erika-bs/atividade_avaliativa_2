from __future__ import annotations
import os
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

from app.config import MONGO_URL,MONGO_DB

# --- DB helpers ---
_client: Optional[AsyncIOMotorClient] = None

def db():
    """
    Abre a conexão com o MongoDB e devolve o banco de dados.
    Não é necessário criar a conexão toda vez, a função guarda em uma variável 
    global (_client) e só cria se ainda não existir.
    """
    global _client
    if _client is None:
        if not MONGO_URL:
            raise RuntimeError("Defina MONGO_URL no .env (string do MongoDB Atlas).")
        _client = AsyncIOMotorClient(MONGO_URL)
    return _client[MONGO_DB]


def iso(dt: datetime) -> str:
    """
    Transforma a data em string no formato ISO.
    Se não houver informação de fuso horário, é colocado UTC por padrão.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def serialize(doc: dict) -> dict:
    """
    Converte o _id, que vem como ObjectId em string.
    Converte o created_at para o formato ISO.
    """
    d = dict(doc)
    if "_id" in d:
        d["_id"] = str(d["_id"])
    if "created_at" in d and isinstance(d["created_at"], datetime):
        d["created_at"] = iso(d["created_at"])
    return d