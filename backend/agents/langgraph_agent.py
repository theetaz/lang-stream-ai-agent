from typing import AsyncIterator, Literal, Optional
from uuid import UUID
from contextvars import ContextVar

from config.settings import settings
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.store.base import BaseStore
from langgraph.graph.message import add_messages

# Context variable to store config for tools to access
_graph_config: ContextVar[Optional[RunnableConfig]] = ContextVar("graph_config", default=None)


def get_llm():
    """Get ChatOpenAI instance with tool binding"""
    api_key = settings.OPENAI_API_KEY
    if not api_key or api_key == "your_openai_api_key_here":
        raise ValueError(
            "OPENAI_API_KEY not set. Please add your OpenAI API key to the .env file"
        )

    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        streaming=True,
        api_key=api_key,
    )


def get_tools(include_memory: bool = False):
    """Get available tools for the agent"""
    from langchain_core.tools import tool

    @tool
    def tavily_search(query: str) -> str:
        """Search the web for current information using Tavily.

        Use this when you need up-to-date information about:
        - Current events, news, weather
        - Sports scores and schedules
        - Stock prices
        - Real-time data

        Args:
            query: The search query

        Returns:
            Search results as a formatted string
        """
        from langchain_tavily import TavilySearch

        search_tool = TavilySearch(
            tavily_api_key=settings.TAVILY_API_KEY,  # Note: parameter name is 'tavily_api_key'
            max_results=3,
            search_depth="advanced",
            include_answer=True,
            include_raw_content=False,
            include_images=False,
        )

        result = search_tool.invoke({"query": query})

        # Format the result nicely
        if isinstance(result, dict):
            output = []
            if result.get("answer"):
                output.append(f"Answer: {result['answer']}\n")

            if result.get("results"):
                output.append("Sources:")
                for i, r in enumerate(result["results"][:3], 1):
                    output.append(f"\n{i}. {r.get('title', 'N/A')}")
                    output.append(f"   {r.get('content', '')[:200]}...")
                    output.append(f"   URL: {r.get('url', '')}")

            return "\n".join(output)

        return str(result)

    tools = [tavily_search]
    
    if include_memory:
        from agents.tools.semantic_memory_tool import get_memory_tools
        from agents.tools.episodic_memory_tool import get_episodic_tools
        from agents.tools.document_search_tool import get_document_tools
        tools.extend(get_memory_tools())
        tools.extend(get_episodic_tools())
        tools.extend(get_document_tools())
    
    return tools


def should_continue(state: MessagesState) -> Literal["tools", END]:
    """Determine whether to use tools or end the conversation"""
    messages = state["messages"]
    last_message = messages[-1]

    # If the LLM makes a tool call, route to the tools node
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    # Otherwise, end the conversation
    return END


async def call_model(
    state: MessagesState,
    config: RunnableConfig,
    *,
    store: Optional[BaseStore] = None
):
    """
    Call the OpenAI model with tools and long-term memory support.
    
    Args:
        state: Current graph state with messages
        config: Runnable config containing user_id and thread_id
        store: Optional store for long-term memory access
    """
    tools = get_tools(include_memory=True)
    llm = get_llm()
    llm_with_tools = llm.bind_tools(tools)

    # Add system message if not already present
    messages = state["messages"]
    
    # Retrieve relevant memories from long-term store if available
    memory_context = ""
    if store and config and config.get("configurable"):
        user_id = config["configurable"].get("user_id")
        if user_id:
            try:
                # Namespace memories by user_id
                namespace = (str(user_id), "memories")
                
                # Search for relevant memories based on the last user message
                if messages:
                    last_message_content = str(messages[-1].content) if hasattr(messages[-1], "content") else ""
                    if last_message_content:
                        memories = await store.asearch(
                            namespace,
                            query=last_message_content,
                            limit=3
                        )
                        
                        if memories:
                            memory_texts = []
                            for mem in memories:
                                mem_value = mem.value if hasattr(mem, "value") else mem
                                if isinstance(mem_value, dict):
                                    content = mem_value.get("content") or mem_value.get("text") or str(mem_value)
                                    memory_type = mem_value.get("memory_type", "")
                                    if memory_type:
                                        memory_texts.append(f"[{memory_type}] {content}")
                                    else:
                                        memory_texts.append(content)
                            
                            if memory_texts:
                                memory_context = "\n## User Memories\n" + "\n".join(memory_texts)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to retrieve memories: {e}")
    
    # Check if session has uploaded files (for document search encouragement)
    has_files = False
    if config and config.get("configurable"):
        thread_id = config["configurable"].get("thread_id")
        if thread_id:
            try:
                from database.db_client import AsyncSessionLocal
                from sqlalchemy import select, func
                from models.uploaded_file import UploadedFile, ProcessingStatus
                
                async with AsyncSessionLocal() as check_db:
                    file_count_query = select(func.count(UploadedFile.id)).where(
                        UploadedFile.session_id == UUID(thread_id),
                        UploadedFile.processing_status == ProcessingStatus.COMPLETED
                    )
                    result = await check_db.execute(file_count_query)
                    file_count = result.scalar() or 0
                    has_files = file_count > 0
            except Exception:
                pass  # Ignore errors, just don't set has_files
    
    # Build system message with memory context
    system_content = (
        "You are a helpful AI assistant with access to tools. "
        "When users upload files or ask about documents, you MUST use the search_user_documents tool to find information in their files. "
        "When users ask questions requiring current information, use tavily_search. "
        "Always provide detailed, helpful responses based on the information you find."
    )
    
    # Add file context if files exist in session
    if has_files:
        system_content += (
            "\n\nIMPORTANT: This conversation has uploaded files. "
            "When the user asks questions, ALWAYS use the search_user_documents tool first to search their uploaded files before responding. "
            "This includes questions like 'what is this file', 'tell me about the document', or any questions that might relate to uploaded content."
        )
    
    if memory_context:
        system_content += memory_context
    
    if not messages or not isinstance(messages[0], SystemMessage):
        system_msg = SystemMessage(content=system_content)
        messages = [system_msg] + messages
    else:
        # Update existing system message with memory context
        messages[0] = SystemMessage(content=system_content)

    response = await llm_with_tools.ainvoke(messages)
    return {"messages": [response]}


async def tools_node_with_config(state: MessagesState, config: RunnableConfig):
    """
    Custom tool node that passes config to tools.
    This ensures user_id and other config values are available to tools.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Log config for debugging
    if config:
        logger.info(f"tools_node_with_config received config: {config}")
        if isinstance(config, dict):
            configurable = config.get("configurable", {})
            user_id = configurable.get("user_id") if isinstance(configurable, dict) else None
            logger.info(f"Extracted user_id from config in tools_node: {user_id}")
    
    # Store config in context variable so tools can access it
    _graph_config.set(config)
    
    try:
        tools = get_tools(include_memory=True)
        tool_node = ToolNode(tools)
        
        # Invoke with config - ToolNode should pass config to tools
        result = await tool_node.ainvoke(state, config)
        return result
    finally:
        # Clear context variable after use
        _graph_config.set(None)


def get_graph(
    checkpointer: Optional[BaseCheckpointSaver] = None,
    store: Optional[BaseStore] = None
):
    """
    Create and compile the LangGraph with tool calling support and memory.

    Graph structure:
    START -> call_model -> [should_continue] -> tools -> call_model -> END
                                              -> END
    
    Args:
        checkpointer: Optional checkpointer for short-term memory (session state)
        store: Optional store for long-term memory (cross-session memories)
    """
    graph = StateGraph(MessagesState)

    # Add nodes
    graph.add_node("call_model", call_model)
    graph.add_node("tools", tools_node_with_config)

    # Set entry point
    graph.add_edge(START, "call_model")

    # Add conditional edge from call_model
    graph.add_conditional_edges(
        "call_model",
        should_continue,
    )

    # After tools, always go back to call_model
    graph.add_edge("tools", "call_model")

    # Compile with both checkpointer (short-term) and store (long-term)
    return graph.compile(checkpointer=checkpointer, store=store)


async def stream_graph(
    user_input: str,
    session_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    use_checkpointing: bool = False,
    previous_messages: Optional[list] = None
) -> AsyncIterator[dict]:
    """
    Stream the graph response with tool calls and tokens.
    Yields events as dictionaries with type and data.
    
    Args:
        user_input: Current user message
        session_id: Optional session ID for checkpointing
        user_id: Optional user ID for long-term memory
        use_checkpointing: Whether to use checkpointing (loads previous state automatically)
        previous_messages: Optional list of previous messages to include if checkpointing disabled
    """
    import logging
    from langchain_core.messages import AIMessage
    from models.chat_message import MessageRole

    logger = logging.getLogger(__name__)

    # Get checkpointer for short-term memory (session state)
    checkpointer = None
    if use_checkpointing and session_id:
        from database.checkpoint_pool import get_async_checkpointer
        checkpointer = await get_async_checkpointer()
    
    # Get store for long-term memory (cross-session memories)
    store = None
    if user_id:
        from database.store_pool import get_async_store
        store = await get_async_store()
    
    graph = get_graph(checkpointer=checkpointer, store=store)

    # Create input with proper message format
    # If checkpointing is disabled but we have previous messages, include them
    messages = []
    if not use_checkpointing and previous_messages:
        # Convert database messages to LangChain messages
        for msg in previous_messages:
            if msg.role == MessageRole.USER:
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == MessageRole.ASSISTANT:
                messages.append(AIMessage(content=msg.content))
    
    # Add current user message
    messages.append(HumanMessage(content=user_input))
    input_data = {"messages": messages}
    
    # Create config with thread_id for checkpointing and user_id for long-term memory
    config = {}
    if session_id or user_id:
        config = {
            "configurable": {
                "thread_id": str(session_id) if session_id else None,
                "user_id": str(user_id) if user_id else None
            }
        }

    current_node = None
    tool_call_active = False
    event_count = 0

    try:
        # Stream events from the graph
        async for event in graph.astream_events(input_data, config=config if config else None, version="v2"):
            event_count += 1
            kind = event.get("event")
            name = event.get("name", "")

            logger.info(f"Event #{event_count}: kind={kind}, name={name}")

            # Track which node we're in
            if kind == "on_chain_start":
                current_node = name
                if name == "tools":
                    tool_call_active = True
                    yield {
                        "type": "tool_start",
                        "data": {"message": "Searching the web..."},
                    }

            # Tool execution started
            if kind == "on_tool_start":
                tool_name = event.get("name", "Unknown tool")
                tool_input = event.get("data", {}).get("input", {})
                logger.info(f"Tool started: {tool_name} with input: {tool_input}")
                yield {
                    "type": "tool_call",
                    "data": {"tool": tool_name, "input": tool_input},
                }

            # Tool execution completed
            if kind == "on_tool_end":
                tool_output = event.get("data", {}).get("output", "")
                logger.info(
                    f"Tool completed with output length: {len(str(tool_output))}"
                )
                yield {
                    "type": "tool_result",
                    "data": {"result": str(tool_output)[:500]},  # Limit result size
                }

            # Track when tools node ends
            if kind == "on_chain_end" and name == "tools":
                tool_call_active = False
                logger.info("Tools node completed")

            # LLM tokens - only stream when not in tool execution
            if kind == "on_chat_model_stream":
                content = event.get("data", {}).get("chunk", {})

                # Stream text content
                if hasattr(content, "content") and content.content:
                    # Only stream final response tokens (after tools if any)
                    yield {"type": "token", "data": {"content": content.content}}

                # Tool calls in the stream (when model decides to use tools)
                if hasattr(content, "tool_call_chunks") and content.tool_call_chunks:
                    for tool_call_chunk in content.tool_call_chunks:
                        if tool_call_chunk.get("name"):
                            yield {
                                "type": "tool_thinking",
                                "data": {"tool_name": tool_call_chunk["name"]},
                            }

        logger.info(f"Stream completed. Total events: {event_count}")

    except Exception as e:
        logger.error(f"Error in stream_graph: {e}", exc_info=True)
        raise
