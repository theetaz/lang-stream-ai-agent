import os
from typing import AsyncIterator, Literal
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import ToolNode


def get_llm():
    """Get ChatOpenAI instance with tool binding"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        raise ValueError(
            "OPENAI_API_KEY not set. Please add your OpenAI API key to the .env file"
        )

    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        streaming=True,
    )


def get_tools():
    """Get available tools for the agent"""
    # Initialize Tavily search tool
    search = TavilySearchResults(
        max_results=3,
        search_depth="advanced",
        include_answer=True,
        include_raw_content=False,
    )
    return [search]


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


def get_graph() -> StateGraph:
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

    return graph.compile()


async def stream_graph(user_input: str) -> AsyncIterator[dict]:
    """
    Stream the graph response with tool calls and tokens.
    Yields events as dictionaries with type and data.
    """
    graph = get_graph()

    # Create input with proper message format
    input_data = {
        "messages": [HumanMessage(content=user_input)]
    }

    # Stream events from the graph
    async for event in graph.astream_events(input_data, version="v2"):
        kind = event.get("event")
        name = event.get("name", "")

        # Tool call started
        if kind == "on_chain_start" and name == "tools":
            yield {
                "type": "tool_start",
                "data": {"message": "Searching the web..."}
            }

        # Tool execution
        if kind == "on_tool_start":
            tool_name = event.get("name", "Unknown tool")
            tool_input = event.get("data", {}).get("input", {})
            yield {
                "type": "tool_call",
                "data": {
                    "tool": tool_name,
                    "input": tool_input
                }
            }

        # Tool result
        if kind == "on_tool_end":
            tool_output = event.get("data", {}).get("output", "")
            yield {
                "type": "tool_result",
                "data": {"result": tool_output}
            }

        # LLM tokens
        if kind == "on_chat_model_stream":
            content = event.get("data", {}).get("chunk", {})
            if hasattr(content, "content") and content.content:
                yield {
                    "type": "token",
                    "data": {"content": content.content}
                }

            # Tool calls in the stream
            if hasattr(content, "tool_call_chunks") and content.tool_call_chunks:
                for tool_call_chunk in content.tool_call_chunks:
                    if tool_call_chunk.get("name"):
                        yield {
                            "type": "tool_thinking",
                            "data": {"tool_name": tool_call_chunk["name"]}
                        }
