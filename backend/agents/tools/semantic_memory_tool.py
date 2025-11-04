from langchain_core.tools import tool
from typing import Literal, Optional
from services.memory_service import memory_service
from common.logger import get_logger

logger = get_logger(__name__)

@tool
async def save_user_memory(
    memory_type: Literal["fact", "preference", "context", "relationship"],
    memory_id: str,
    content: str,
    metadata: Optional[dict] = None
) -> str:
    """
    Store important information about the user for future conversations.
    
    Use when user shares:
    - fact: Personal info (name: John, location: NYC, job: engineer)
    - preference: Likes/dislikes (prefers Python, dislikes verbose code)
    - context: Current situation (working on AI chatbot, deadline next week)
    - relationship: People/places (manager: Sarah, team: AI Lab)
    
    Args:
        memory_type: Type of memory (fact/preference/context/relationship)
        memory_id: Unique identifier (e.g., "user_name", "programming_pref")
        content: The actual memory text
        metadata: Optional additional data
    
    Returns:
        Confirmation message
    """
    logger.info(f"Tool called: save_user_memory - {memory_type}: {memory_id}")
    
    return f"Saved {memory_type} memory: {memory_id} - '{content}'"

@tool
async def recall_user_memories(query: str, memory_type: Optional[str] = None) -> str:
    """
    Search user's stored memories for relevant information.
    Call this before responding to check what you know about the user.
    
    Args:
        query: What to search for
        memory_type: Optional filter (fact, preference, context, relationship)
    
    Returns:
        Relevant memories as formatted text
    """
    logger.info(f"Tool called: recall_user_memories - query: {query}")
    
    return "No relevant memories found yet. This is an early prototype."

def get_memory_tools():
    """Get all memory-related tools"""
    return [save_user_memory, recall_user_memories]

