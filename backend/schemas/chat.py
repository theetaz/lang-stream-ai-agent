from typing import Any, Dict, Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    input: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    output: str
    metadata: Optional[Dict[str, Any]] = None
