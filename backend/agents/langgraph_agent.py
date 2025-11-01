import os
from typing import AsyncIterator
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage


def get_llm():
    """Get ChatOpenAI instance"""
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


def call_model(state: MessagesState):
    """Call the OpenAI model"""
    llm = get_llm()
    response = llm.invoke(state["messages"])
    return {"messages": [response]}


def get_graph() -> StateGraph:
    """Create and compile the LangGraph"""
    graph = StateGraph(MessagesState)
    graph.add_node("call_model", call_model)
    graph.add_edge(START, "call_model")
    graph.add_edge("call_model", END)
    return graph.compile()


async def stream_graph(user_input: str) -> AsyncIterator[str]:
    """
    Stream the graph response token by token.
    Uses LangGraph's astream_events for real-time streaming.
    """
    graph = get_graph()

    # Create input with proper message format
    input_data = {
        "messages": [HumanMessage(content=user_input)]
    }

    # Stream events from the graph
    async for event in graph.astream_events(input_data, version="v2"):
        kind = event.get("event")

        # We want to stream the tokens as they come from the LLM
        if kind == "on_chat_model_stream":
            content = event.get("data", {}).get("chunk", {})
            if hasattr(content, "content") and content.content:
                # Yield each token as it arrives
                yield content.content
