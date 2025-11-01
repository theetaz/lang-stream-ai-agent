import json
from typing import AsyncIterator
from agents.langgraph_agent import get_graph, stream_graph
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()


class ChatRequest(BaseModel):
    input: str


class ChatResponse(BaseModel):
    response: str


async def event_stream(user_input: str) -> AsyncIterator[str]:
    """
    Generate Server-Sent Events stream for chat responses
    """
    try:
        async for chunk in stream_graph(user_input):
            # Format as SSE
            data = json.dumps({"content": chunk})
            yield f"data: {data}\n\n"

        # Send completion event
        yield f"data: {json.dumps({'done': True})}\n\n"

    except Exception as e:
        # Send error event
        error_data = json.dumps({"error": str(e)})
        yield f"data: {error_data}\n\n"


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint using Server-Sent Events (SSE)
    """
    return StreamingResponse(
        event_stream(request.input),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering for nginx
        },
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Non-streaming chat endpoint (fallback)
    """
    graph = get_graph()
    result = graph.invoke({"messages": [{"role": "user", "content": request.input}]})

    # Extract the AI response from the result
    messages = result.get("messages", [])
    if messages:
        ai_message = messages[-1]
        # Handle both dict and AIMessage object
        if hasattr(ai_message, "content"):
            response_text = ai_message.content
        elif isinstance(ai_message, dict):
            response_text = ai_message.get("content", "I'm sorry, I couldn't process your request.")
        else:
            response_text = str(ai_message)
    else:
        response_text = "I'm sorry, I couldn't process your request."

    return ChatResponse(response=response_text)


@router.post("/agent")
async def run_agent():
    """
    Legacy agent endpoint (kept for backwards compatibility)
    """
    graph = get_graph()
    response = graph.invoke({"messages": [{"role": "user", "content": "hi!"}]})
    return {"response": response}
