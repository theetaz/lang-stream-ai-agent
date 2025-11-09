from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from uuid import UUID

class ChatSessionCreate(BaseModel):
    title: Optional[str] = None

class ChatSessionUpdate(BaseModel):
    title: Optional[str] = None
    is_archived: Optional[bool] = None
    is_pinned: Optional[bool] = None

class ChatSessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: Optional[str]
    last_message_at: Optional[datetime]
    is_archived: bool
    is_pinned: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

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
    files: Optional[list["UploadedFileResponse"]] = None

    model_config = ConfigDict(from_attributes=True)


# Import here to avoid circular dependency
from schemas.file import UploadedFileResponse

