from api.v1.chat.service import ChatService
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


def get_chat_service() -> ChatService:
    """Dependency to get ChatService instance."""
    return ChatService()


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
):
    """Streaming chat endpoint using Server-Sent Events (SSE)."""
    return StreamingResponse(
        service.event_stream(request.input),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering for nginx
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
