from __future__ import annotations
from pydantic import BaseModel, Field

class MessageIn(BaseModel):
    username: str = Field(..., max_length=50)
    content: str = Field(..., max_length=1000)

class MessageOut(BaseModel):
    _id: str
    room: str
    username: str
    content: str
    # serialize() já transforma datetime em ISO string
    created_at: str