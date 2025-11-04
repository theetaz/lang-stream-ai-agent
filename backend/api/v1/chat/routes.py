from api.v1.chat.service import ChatService
from api.v1.chat.session_service import session_service
from api.v1.chat.message_service import message_service
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from schemas.chat import ChatRequest, ChatResponse
from schemas.chat_session import (
    ChatSessionCreate,
    ChatSessionUpdate,
    ChatSessionResponse,
    ChatMessageResponse
)
from database.db_client import get_db
from auth.utils import get_current_user
from models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from common.response import APIResponse, success_response
from uuid import UUID
from typing import List, Optional

router = APIRouter(prefix="/chat", tags=["chat"])


def get_chat_service() -> ChatService:
    """Dependency to get ChatService instance."""
    return ChatService()


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    session_id: Optional[UUID] = None,
    service: ChatService = Depends(get_chat_service),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Streaming chat endpoint using Server-Sent Events (SSE)."""
    if session_id:
        await session_service.get_session(db, session_id, current_user.id)
    
    return StreamingResponse(
        service.event_stream(
            request.input,
            session_id=session_id,
            user_id=current_user.id,
            db=db
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
):
    """Non-streaming chat endpoint (fallback)."""
    return await service.chat(request)


@router.post("/agent")
async def run_agent(
    service: ChatService = Depends(get_chat_service),
):
    """Legacy agent endpoint (kept for backwards compatibility)."""
    return await service.run_agent()


@router.post("/sessions", response_model=APIResponse[ChatSessionResponse])
async def create_session(
    data: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    session = await session_service.create_session(db, current_user.id, data.title)
    return success_response(
        ChatSessionResponse.model_validate(session),
        message="Session created successfully"
    )


@router.get("/sessions", response_model=APIResponse[List[ChatSessionResponse]])
async def get_sessions(
    archived: bool = False,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    sessions = await session_service.get_sessions(db, current_user.id, archived, limit, offset)
    return success_response(
        [ChatSessionResponse.model_validate(s) for s in sessions],
        message="Sessions fetched successfully"
    )


@router.get("/sessions/{session_id}", response_model=APIResponse[ChatSessionResponse])
async def get_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    session = await session_service.get_session(db, session_id, current_user.id)
    return success_response(
        ChatSessionResponse.model_validate(session),
        message="Session fetched successfully"
    )


@router.patch("/sessions/{session_id}", response_model=APIResponse[ChatSessionResponse])
async def update_session(
    session_id: UUID,
    data: ChatSessionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if data.title:
        session = await session_service.update_title(db, session_id, current_user.id, data.title)
    elif data.is_archived is not None:
        session = await session_service.archive_session(db, session_id, current_user.id)
    else:
        session = await session_service.get_session(db, session_id, current_user.id)
    
    return success_response(
        ChatSessionResponse.model_validate(session),
        message="Session updated successfully"
    )


@router.delete("/sessions/{session_id}", response_model=APIResponse[dict])
async def delete_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await session_service.delete_session(db, session_id, current_user.id)
    return success_response(
        {"session_id": str(session_id)},
        message="Session deleted successfully"
    )


@router.get("/sessions/{session_id}/messages", response_model=APIResponse[List[ChatMessageResponse]])
async def get_messages(
    session_id: UUID,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await session_service.get_session(db, session_id, current_user.id)
    messages = await message_service.get_messages(db, session_id, limit, offset)
    return success_response(
        [ChatMessageResponse.model_validate(m) for m in messages],
        message="Messages fetched successfully"
    )
