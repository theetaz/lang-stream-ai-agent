import asyncio
import json
from typing import AsyncIterator

from agents.langgraph_agent import get_graph, stream_graph
from schemas.chat import ChatRequest, ChatResponse


class ChatService:
    """Service for chat operations."""

    async def event_stream(self, user_input: str) -> AsyncIterator[str]:
        """
        Generate Server-Sent Events stream for chat responses.
        Streams tokens and tool call events in real-time.
        """
        try:
            # Send initial connection confirmation
            yield f": connected\n\n"

            token_count = 0
            has_content = False

            async for event in stream_graph(user_input):
                event_type = event.get("type")
                event_data = event.get("data", {})

                # Handle different event types
                if event_type == "token":
                    # Regular token from LLM
                    has_content = True
                    data = json.dumps(
                        {
                            "type": "content",
                            "content": event_data.get("content", ""),
                            "token": token_count,
                        }
                    )
                    yield f"data: {data}\n\n"
                    token_count += 1

                elif event_type == "tool_start":
                    # Tool execution started
                    data = json.dumps(
                        {
                            "type": "tool_start",
                            "message": event_data.get("message", "Using tools..."),
                        }
                    )
                    yield f"data: {data}\n\n"

                elif event_type == "tool_thinking":
                    # AI is thinking about using a tool
                    data = json.dumps(
                        {
                            "type": "tool_thinking",
                            "tool_name": event_data.get("tool_name", ""),
                        }
                    )
                    yield f"data: {data}\n\n"

                elif event_type == "tool_call":
                    # Tool is being called
                    data = json.dumps(
                        {
                            "type": "tool_call",
                            "tool": event_data.get("tool", ""),
                            "input": event_data.get("input", {}),
                        }
                    )
                    yield f"data: {data}\n\n"

                elif event_type == "tool_result":
                    # Tool execution completed
                    data = json.dumps(
                        {"type": "tool_result", "result": event_data.get("result", "")}
                    )
                    yield f"data: {data}\n\n"

                # Flush immediately
                await asyncio.sleep(0)

            # If no content was generated, send a message
            if not has_content:
                data = json.dumps(
                    {
                        "type": "content",
                        "content": "I've searched for the information but couldn't generate a response. Please try again.",
                        "token": 0,
                    }
                )
                yield f"data: {data}\n\n"

            # Send completion event
            yield f"data: {json.dumps({'type': 'done', 'total_tokens': token_count})}\n\n"

        except asyncio.TimeoutError:
            # Timeout error
            error_data = json.dumps(
                {
                    "type": "error",
                    "error": "Request timed out. The tool took too long to respond.",
                }
            )
            yield f"data: {error_data}\n\n"
        except Exception as e:
            # Send error event
            import traceback

            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            error_data = json.dumps({"type": "error", "error": error_msg})
            yield f"data: {error_data}\n\n"

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Non-streaming chat endpoint (fallback)."""
        graph = get_graph()
        result = graph.invoke(
            {"messages": [{"role": "user", "content": request.input}]}
        )

        # Extract the AI response from the result
        messages = result.get("messages", [])
        if messages:
            ai_message = messages[-1]
            # Handle both dict and AIMessage object
            if hasattr(ai_message, "content"):
                response_text = ai_message.content
            elif isinstance(ai_message, dict):
                response_text = ai_message.get(
                    "content", "I'm sorry, I couldn't process your request."
                )
            else:
                response_text = str(ai_message)
        else:
            response_text = "I'm sorry, I couldn't process your request."

        return ChatResponse(response=response_text)

    async def run_agent(self) -> dict:
        """Legacy agent endpoint (kept for backwards compatibility)."""
        graph = get_graph()
        response = graph.invoke({"messages": [{"role": "user", "content": "hi!"}]})
        return {"response": response}
