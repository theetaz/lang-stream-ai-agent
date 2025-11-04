from typing import AsyncIterator, Literal, Optional
from uuid import UUID

from config.settings import settings
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.base import BaseCheckpointSaver


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


def get_tools():
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

    return [tavily_search]


def should_continue(state: MessagesState) -> Literal["tools", END]:
    """Determine whether to use tools or end the conversation"""
    messages = state["messages"]
    last_message = messages[-1]

    # If the LLM makes a tool call, route to the tools node
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    # Otherwise, end the conversation
    return END


def call_model(state: MessagesState):
    """Call the OpenAI model with tools"""
    tools = get_tools()
    llm = get_llm()
    llm_with_tools = llm.bind_tools(tools)

    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


def get_graph(checkpointer: Optional[BaseCheckpointSaver] = None):
    """
    Create and compile the LangGraph with tool calling support.

    Graph structure:
    START -> call_model -> [should_continue] -> tools -> call_model -> END
                                              -> END
    """
    tools = get_tools()
    tool_node = ToolNode(tools)

    graph = StateGraph(MessagesState)

    # Add nodes
    graph.add_node("call_model", call_model)
    graph.add_node("tools", tool_node)

    # Set entry point
    graph.add_edge(START, "call_model")

    # Add conditional edge from call_model
    graph.add_conditional_edges(
        "call_model",
        should_continue,
    )

    # After tools, always go back to call_model
    graph.add_edge("tools", "call_model")

    return graph.compile(checkpointer=checkpointer)


async def stream_graph(
    user_input: str,
    session_id: Optional[UUID] = None,
    user_id: Optional[int] = None,
    checkpointer: Optional[BaseCheckpointSaver] = None
) -> AsyncIterator[dict]:
    """
    Stream the graph response with tool calls and tokens.
    Yields events as dictionaries with type and data.
    """
    import logging

    logger = logging.getLogger(__name__)

    graph = get_graph(checkpointer=checkpointer)

    # Create input with proper message format
    input_data = {"messages": [HumanMessage(content=user_input)]}
    
    # Create config with thread_id for checkpointing
    config = {}
    if session_id and checkpointer:
        config = {
            "configurable": {
                "thread_id": str(session_id),
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
