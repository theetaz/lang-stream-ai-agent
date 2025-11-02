"""
Pydantic schemas for Chat API endpoints.
"""
from pydantic import BaseModel


class ChatRequest(BaseModel):
    input: str


class ChatResponse(BaseModel):
    response: str

