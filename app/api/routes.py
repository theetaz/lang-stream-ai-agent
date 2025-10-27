from agents.langgraph_agent import AIAgent
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class AgentRequest(BaseModel):
    input: str


@router.post("/agent")
async def run_agent(request: AgentRequest):
    agent = AIAgent()
    response = agent.process_input(request.input)
    return {"response": response}
