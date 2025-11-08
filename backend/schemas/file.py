from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from uuid import UUID

class UploadedFileResponse(BaseModel):
    id: UUID
    user_id: str
    session_id: UUID
    message_id: Optional[UUID]
    filename: str
    file_type: Optional[str]
    file_size: Optional[int]
    processing_status: str
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)

class FileChunkResponse(BaseModel):
    id: UUID
    file_id: UUID
    chunk_index: int
    content: str
    meta: Optional[dict]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

