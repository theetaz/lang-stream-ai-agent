from typing import Any, Dict, Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    input: str


class ChatResponse(BaseModel):
    output: str
    metadata: Optional[Dict[str, Any]] = None
