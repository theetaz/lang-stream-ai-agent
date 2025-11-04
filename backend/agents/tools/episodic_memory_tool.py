from langchain_core.tools import tool
from common.logger import get_logger

logger = get_logger(__name__)

@tool
async def save_successful_approach(
    episode_id: str,
    task: str,
    approach: str,
    outcome: str
) -> str:
    """
    Save a successful approach for future reference.
    Use after completing a task successfully.
    
    Args:
        episode_id: Unique identifier (e.g., "api_integration_2024_01")
        task: What was being accomplished
        approach: How it was done
        outcome: The result
    
    Returns:
        Confirmation message
    """
    logger.info(f"Tool called: save_successful_approach - {episode_id}")
    
    return f"Saved episode: {episode_id}"

@tool
async def recall_similar_experiences(task_description: str) -> str:
    """
    Find similar past experiences to learn from.
    Use when starting a new task.
    
    Args:
        task_description: Description of the current task
    
    Returns:
        Similar past experiences as formatted text
    """
    logger.info(f"Tool called: recall_similar_experiences - task: {task_description}")
    
    return "No similar past experiences found yet. This is an early prototype."

def get_episodic_tools():
    """Get all episodic memory tools"""
    return [save_successful_approach, recall_similar_experiences]

