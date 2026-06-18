from datetime import datetime

from pydantic import BaseModel


class ChatRequest(BaseModel):
    diagnosis_id: int
    message: str


class ChatMessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    session_id: int
    messages: list[ChatMessageOut]
