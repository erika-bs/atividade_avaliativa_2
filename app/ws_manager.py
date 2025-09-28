from __future__ import annotations
from typing import Dict, Set
from fastapi import WebSocket

# --- WebSocket room manager ---
class WSManager:
    def __init__(self):
        self.rooms: Dict[str, Set[WebSocket]] = {}

    async def connect(self, room: str, ws: WebSocket):
        """
        Aceita a conexão de um usuário e coloca o websocket dele na
        lista de conexões da sala escolhida.
        """
        await ws.accept()
        self.rooms.setdefault(room, set()).add(ws)

    def disconnect(self, room: str, ws: WebSocket):
        """
        Tira a conexão da sala quando o usuário sai ou acontece algum erro.
        Se a sala ficar sem ninguém, ela é apagada da lista de salas.
        """
        conns = self.rooms.get(room)
        if conns and ws in conns:
            conns.remove(ws)
            if not conns:
                self.rooms.pop(room, None)

    async def broadcast(self, room: str, payload: dict):
        """
        Envia uma mensagem (payload) para todos os usuários que estão dentro da sala.
        Se alguma conexão não responder, ela é removida automaticamente.
        """
        for ws in list(self.rooms.get(room, [])):
            try:
                await ws.send_json(payload)
            except Exception:
                self.disconnect(room, ws)