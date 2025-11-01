from agents.langgraph_agent import get_graph
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ChatRequest(BaseModel):
    input: str


class ChatResponse(BaseModel):
    response: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint that accepts user input and returns AI response
    """
    graph = get_graph()
    result = graph.invoke({"messages": [{"role": "user", "content": request.input}]})

    # Extract the AI response from the result
    messages = result.get("messages", [])
    if messages:
        ai_message = messages[-1]
        # Handle both dict and AIMessage object
        if hasattr(ai_message, "content"):
            response_text = ai_message.content
        elif isinstance(ai_message, dict):
            response_text = ai_message.get("content", "I'm sorry, I couldn't process your request.")
        else:
            response_text = str(ai_message)
    else:
        response_text = "I'm sorry, I couldn't process your request."

    return ChatResponse(response=response_text)


@router.post("/agent")
async def run_agent():
    """
    Legacy agent endpoint (kept for backwards compatibility)
    """
    graph = get_graph()
    response = graph.invoke({"messages": [{"role": "user", "content": "hi!"}]})
    return {"response": response}
