from typing import TypedDict

from langgraph.graph import END, StateGraph


class AgentState(TypedDict):
    input: str
    output: str


class AIAgent:
    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(AgentState)

        def process_node(state: AgentState) -> AgentState:
            return {"input": state["input"], "output": f"Processed: {state['input']}"}

        graph.add_node("process", process_node)
        graph.set_entry_point("process")
        graph.add_edge("process", END)

        return graph.compile()

    def process_input(self, input_text: str) -> str:
        result = self.graph.invoke({"input": input_text})
        return result["output"]
