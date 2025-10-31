from langgraph.graph import END, START, MessagesState, StateGraph


def _mock_llm(state: MessagesState):
    return {"messages": [{"role": "ai", "content": "hello world"}]}


def get_graph() -> StateGraph:
    graph = StateGraph(MessagesState)
    graph.add_node(_mock_llm)
    graph.add_edge(START, "_mock_llm")
    graph.add_edge("_mock_llm", END)
    graph = graph.compile()

    return graph
