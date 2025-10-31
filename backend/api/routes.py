from agents.langgraph_agent import get_graph
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


@router.post("/agent")
async def run_agent():
    graph = get_graph()
    response = graph.invoke({"messages": [{"role": "user", "content": "hi!"}]})
    return {"response": response}
