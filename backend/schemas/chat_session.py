from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID

class ChatSessionCreate(BaseModel):
    title: Optional[str] = None

class ChatSessionUpdate(BaseModel):
    title: Optional[str] = None
    is_archived: Optional[bool] = None

class ChatSessionResponse(BaseModel):
    id: UUID
    user_id: str
    title: Optional[str]
    last_message_at: Optional[datetime]
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ChatMessageCreate(BaseModel):
    content: str
    meta: Optional[dict] = None

class ChatMessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    meta: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True

