import asyncio
import json
from typing import AsyncIterator, Optional
from uuid import UUID

from agents.langgraph_agent import get_graph, stream_graph

# Checkpointer is now loaded lazily within stream_graph
from api.v1.chat.message_service import message_service
from api.v1.chat.session_service import session_service
from models.chat_message import MessageRole
from schemas.chat import ChatRequest, ChatResponse
from sqlalchemy.ext.asyncio import AsyncSession


class ChatService:
    """Service for chat operations."""

    async def event_stream(
        self,
        user_input: str,
        session_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        db: Optional[AsyncSession] = None,
    ) -> AsyncIterator[str]:
        """
        Generate Server-Sent Events stream for chat responses.
        Streams tokens and tool call events in real-time.
        """
        try:
            # Load previous messages for context if session_id provided
            previous_messages = []
            if session_id and db:
                # Get last 20 messages for context
                previous_messages = await message_service.get_last_n_messages(
                    db, session_id, n=20
                )

            # Save user message to database if session_id provided
            user_message_id = None
            if session_id and db:
                user_message = await message_service.save_message(
                    db, session_id, MessageRole.USER, user_input
                )
                user_message_id = user_message.id
                await session_service.update_last_message_at(db, session_id)

            # Send initial connection confirmation
            yield f": connected\n\n"

            token_count = 0
            has_content = False
            assistant_response = ""

            async for event in stream_graph(
                user_input,
                session_id=session_id,
                user_id=user_id,
                use_checkpointing=bool(session_id),
                previous_messages=(
                    previous_messages if not bool(session_id) else None
                ),  # Only load if checkpointing disabled
            ):
                event_type = event.get("type")
                event_data = event.get("data", {})

                # Handle different event types
                if event_type == "token":
                    # Regular token from LLM
                    has_content = True
                    content = event_data.get("content", "")
                    assistant_response += content
                    data = json.dumps(
                        {
                            "type": "content",
                            "content": content,
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

            # Save assistant response to database if session_id provided
            if session_id and db and assistant_response:
                await message_service.save_message(
                    db, session_id, MessageRole.ASSISTANT, assistant_response
                )
                await session_service.update_last_message_at(db, session_id)

                MAX_MESSAGE_COUNT_THRESHOLD = 3
                # Generate or update title if needed
                message_count = await message_service.count_messages(db, session_id)
                session = await session_service.get_session(db, session_id, user_id)

                # Generate title if:
                # 1. Session still has default title ("New Chat") OR
                # 2. Message count is 3 (first title generation) OR
                # 3. Message count is a multiple of 10 (periodic updates)
                should_generate_title = (
                    message_count == MAX_MESSAGE_COUNT_THRESHOLD
                    or (message_count > MAX_MESSAGE_COUNT_THRESHOLD)
                )
                if should_generate_title:
                    from api.v1.chat.title_service import title_generator

                    # Generate title in background task with proper error handling
                    async def generate_title_task():
                        try:
                            # Create a new db session for the background task
                            from database.db_client import AsyncSessionLocal

                            async with AsyncSessionLocal() as bg_db:
                                await title_generator.generate_title(
                                    bg_db, session_id, user_id
                                )
                        except Exception as e:
                            import traceback

                            from common.logger import get_logger

                            logger = get_logger(__name__)
                            logger.error(
                                f"Failed to generate title for session {session_id}: {e}\n{traceback.format_exc()}"
                            )

                    # Run in background without blocking the response
                    asyncio.create_task(generate_title_task())

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
