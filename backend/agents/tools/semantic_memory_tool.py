from typing import Literal, Optional
from uuid import uuid4

from common.logger import get_logger
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.store.base import BaseStore

logger = get_logger(__name__)


# Import the context variable from langgraph_agent
def _get_graph_config():
    """Get config from context variable set by tools_node_with_config."""
    try:
        from agents.langgraph_agent import _graph_config

        return _graph_config.get()
    except Exception:
        return None


def _get_user_id_from_config(config: Optional[RunnableConfig] = None) -> Optional[str]:
    """Extract user_id from config if available.

    Tries multiple sources:
    1. From passed config parameter
    2. From context variable (set by tools_node_with_config)
    """
    # First try the passed config
    if config:
        if isinstance(config, dict):
            configurable = config.get("configurable", {})
            if isinstance(configurable, dict):
                user_id = configurable.get("user_id")
                if user_id:
                    logger.info(f"Found user_id from config dict: {user_id}")
                    return str(user_id)
        elif hasattr(config, "get"):
            configurable = config.get("configurable", {})
            if isinstance(configurable, dict):
                user_id = configurable.get("user_id")
                if user_id:
                    logger.info(f"Found user_id from config object: {user_id}")
                    return str(user_id)

    # If not found, try to get from context variable
    try:
        context_config = _get_graph_config()
        if context_config:
            if isinstance(context_config, dict):
                configurable = context_config.get("configurable", {})
                if isinstance(configurable, dict):
                    user_id = configurable.get("user_id")
                    if user_id:
                        logger.info(f"Found user_id from context variable: {user_id}")
                        return str(user_id)
            elif hasattr(context_config, "get"):
                configurable = context_config.get("configurable", {})
                if isinstance(configurable, dict):
                    user_id = configurable.get("user_id")
                    if user_id:
                        logger.info(
                            f"Found user_id from context variable (hasattr): {user_id}"
                        )
                        return str(user_id)
    except Exception as e:
        logger.debug(f"Could not get config from context variable: {e}")

    logger.warning("Could not extract user_id from config")
    return None


async def _get_store() -> Optional[BaseStore]:
    """Get the store instance from the pool."""
    try:
        from database.store_pool import get_async_store

        return await get_async_store()
    except Exception as e:
        logger.error(f"Failed to get store: {e}")
        return None


@tool
async def save_user_memory(
    memory_type: Literal["fact", "preference", "context", "relationship"],
    memory_id: str,
    content: str,
    metadata: Optional[dict] = None,
    config: Optional[RunnableConfig] = None,
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
        config: RunnableConfig containing store and user_id

    Returns:
        Confirmation message
    """
    logger.info(f"Tool called: save_user_memory - {memory_type}: {memory_id}")

    try:
        # Get user_id from config
        user_id = _get_user_id_from_config(config)

        if not user_id:
            logger.warning("user_id not available in config. Memory not saved.")
            return f"User ID not available. Would save: {memory_type} memory: {memory_id} - '{content}'"

        # Get store instance
        store = await _get_store()
        if not store:
            logger.warning("Store not available. Memory not saved.")
            return f"Memory store not available. Would save: {memory_type} memory: {memory_id} - '{content}'"

        # Namespace memories by user_id
        namespace = (str(user_id), "memories")

        # Create memory data structure
        memory_data = {
            "content": content,
            "memory_type": memory_type,
            "memory_id": memory_id,
            "metadata": metadata or {},
        }

        # Use memory_id as the key, or generate UUID if needed
        key = memory_id or str(uuid4())

        # Save to store
        await store.aput(namespace, key, memory_data)

        logger.info(f"Successfully saved memory {key} for user {user_id}")
        return f"Saved {memory_type} memory: {memory_id} - '{content}'"

    except Exception as e:
        logger.error(f"Error saving memory: {e}", exc_info=True)
        return f"Error saving memory: {str(e)}"


@tool
async def recall_user_memories(
    query: str,
    memory_type: Optional[str] = None,
    config: Optional[RunnableConfig] = None,
) -> str:
    """
    Search user's stored memories for relevant information.
    Call this before responding to check what you know about the user.

    Args:
        query: What to search for
        memory_type: Optional filter (fact, preference, context, relationship)
        config: RunnableConfig containing store and user_id

    Returns:
        Relevant memories as formatted text
    """
    logger.info(
        f"Tool called: recall_user_memories - query: {query}, type: {memory_type}"
    )

    try:
        # Get user_id from config
        user_id = _get_user_id_from_config(config)

        if not user_id:
            logger.warning("user_id not available in config. Cannot recall memories.")
            return "User ID not available. Cannot recall memories."

        # Get store instance
        store = await _get_store()
        if not store:
            logger.warning("Store not available. Cannot recall memories.")
            return "Memory store not available. Cannot recall memories."

        # Namespace memories by user_id
        namespace = (str(user_id), "memories")

        # Search memories using semantic search
        memories = await store.asearch(namespace, query=query, limit=5)

        if not memories:
            return "No relevant memories found."

        # Format memories
        memory_texts = []
        for mem in memories:
            mem_value = mem.value if hasattr(mem, "value") else mem
            if isinstance(mem_value, dict):
                content = mem_value.get("content", "")
                mem_type = mem_value.get("memory_type", "")
                mem_id = mem_value.get("memory_id", "")

                if memory_type and mem_type != memory_type:
                    continue  # Filter by type if specified

                if mem_type:
                    memory_texts.append(f"[{mem_type}] {mem_id}: {content}")
                else:
                    memory_texts.append(f"{mem_id}: {content}")

        if not memory_texts:
            return (
                f"No memories found matching type '{memory_type}'."
                if memory_type
                else "No relevant memories found."
            )

        result = "## Relevant Memories\n" + "\n".join(memory_texts)
        logger.info(f"Found {len(memory_texts)} relevant memories")
        return result

    except Exception as e:
        logger.error(f"Error recalling memories: {e}", exc_info=True)
        return f"Error recalling memories: {str(e)}"


def get_memory_tools():
    """Get all memory-related tools"""
    return [save_user_memory, recall_user_memories]
