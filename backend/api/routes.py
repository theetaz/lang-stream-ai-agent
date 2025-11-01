import json
import asyncio
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
    Generate Server-Sent Events stream for chat responses.
    Streams tokens and tool call events in real-time.
    """
    try:
        # Send initial connection confirmation
        yield f": connected\n\n"

        token_count = 0
        async for event in stream_graph(user_input):
            event_type = event.get("type")
            event_data = event.get("data", {})

            # Handle different event types
            if event_type == "token":
                # Regular token from LLM
                data = json.dumps({
                    "type": "content",
                    "content": event_data.get("content", ""),
                    "token": token_count
                })
                yield f"data: {data}\n\n"
                token_count += 1

            elif event_type == "tool_start":
                # Tool execution started
                data = json.dumps({
                    "type": "tool_start",
                    "message": event_data.get("message", "Using tools...")
                })
                yield f"data: {data}\n\n"

            elif event_type == "tool_thinking":
                # AI is thinking about using a tool
                data = json.dumps({
                    "type": "tool_thinking",
                    "tool_name": event_data.get("tool_name", "")
                })
                yield f"data: {data}\n\n"

            elif event_type == "tool_call":
                # Tool is being called
                data = json.dumps({
                    "type": "tool_call",
                    "tool": event_data.get("tool", ""),
                    "input": event_data.get("input", {})
                })
                yield f"data: {data}\n\n"

            elif event_type == "tool_result":
                # Tool execution completed
                data = json.dumps({
                    "type": "tool_result",
                    "result": event_data.get("result", "")
                })
                yield f"data: {data}\n\n"

            # Small delay to ensure proper flushing
            await asyncio.sleep(0)

        # Send completion event
        yield f"data: {json.dumps({'type': 'done', 'total_tokens': token_count})}\n\n"

    except Exception as e:
        # Send error event
        error_data = json.dumps({"type": "error", "error": str(e)})
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
