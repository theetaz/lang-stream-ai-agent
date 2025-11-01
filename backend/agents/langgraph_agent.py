import os
from typing import AsyncIterator
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
from langchain_core.messages import HumanMessage, AIMessage


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
    """Stream the graph response"""
    llm = get_llm()
    graph = get_graph()

    # Stream the response
    async for chunk in llm.astream(user_input):
        if chunk.content:
            yield chunk.content
