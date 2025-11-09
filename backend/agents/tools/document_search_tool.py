from typing import Optional
from uuid import UUID
from langchain_core.tools import tool
from langchain_core.runnables.config import RunnableConfig
from common.logger import get_logger

logger = get_logger(__name__)

# Import the context variable from langgraph_agent
def _get_graph_config():
    """Get config from context variable set by tools_node_with_config."""
    try:
        from agents.langgraph_agent import _graph_config
        return _graph_config.get()
    except Exception:
        return None

def _extract_user_and_session_id(config: Optional[RunnableConfig] = None) -> tuple[Optional[UUID], Optional[UUID]]:
    """Extract user_id and session_id from config or context variable."""
    user_id = None
    session_id = None
    
    # First try the passed config
    if config:
        if isinstance(config, dict):
            configurable = config.get("configurable", {})
            if isinstance(configurable, dict):
                user_id_str = configurable.get("user_id")
                session_id_str = configurable.get("thread_id")
                
                if user_id_str:
                    try:
                        user_id = UUID(user_id_str)
                    except (ValueError, TypeError):
                        logger.error(f"Failed to convert user_id_str to UUID: {user_id_str}")
                
                if session_id_str:
                    try:
                        session_id = UUID(session_id_str)
                    except (ValueError, TypeError):
                        logger.error(f"Failed to convert session_id_str to UUID: {session_id_str}")
    
    # If not found, try context variable
    if not user_id or not session_id:
        try:
            context_config = _get_graph_config()
            if context_config:
                logger.info(f"Got config from context variable in document_search_tool: {context_config}")
                if isinstance(context_config, dict):
                    configurable = context_config.get("configurable", {})
                    if isinstance(configurable, dict):
                        if not user_id:
                            user_id_str = configurable.get("user_id")
                            if user_id_str:
                                try:
                                    user_id = UUID(user_id_str)
                                except (ValueError, TypeError):
                                    pass
                        if not session_id:
                            session_id_str = configurable.get("thread_id")
                            if session_id_str:
                                try:
                                    session_id = UUID(session_id_str)
                                except (ValueError, TypeError):
                                    pass
        except Exception as e:
            logger.debug(f"Could not get config from context variable: {e}")
    
    return user_id, session_id

async def _search_documents_impl(query: str, config: Optional[RunnableConfig] = None, limit: int = 5) -> str:
    """Internal implementation of document search"""
    try:
        from database.db_client import AsyncSessionLocal
        from api.v1.chat.rag_service import rag_service
        
        # Extract user_id and session_id from config or context variable
        user_id, session_id = _extract_user_and_session_id(config)
        
        logger.info(f"🔍 Document search - user_id: {user_id}, session_id: {session_id}, query: '{query}'")
        
        if not user_id:
            logger.error("User context not available from config or context variable")
            return "Unable to search documents: User context not available."
        
        async with AsyncSessionLocal() as db:
            # Search across all user sessions by default for better context
            chunks = await rag_service.search_documents(
                db=db,
                user_id=user_id,
                query=query,
                session_id=session_id,
                limit=limit,
                search_all_sessions=True  # Search across all sessions for comprehensive results
            )
            
            logger.info(f"RAG service returned {len(chunks)} chunks")
            
            if not chunks:
                logger.warning("No chunks found - returning error message to AI")
                return "No relevant information found in your uploaded documents. Try uploading files first, then ask me about them once they're processed."
            
            # Format results nicely
            results = []
            results.append(f"Found {len(chunks)} relevant excerpts from your documents:\n")
            
            for i, chunk in enumerate(chunks, 1):
                try:
                    filename = chunk.file.filename if chunk.file else "Unknown file"
                    content = chunk.content[:400]  # Limit content length
                    if len(chunk.content) > 400:
                        content += "..."
                    
                    results.append(f"\n📄 Source {i}: {filename}")
                    results.append(f"{content}\n")
                    logger.info(f"  Added chunk {i} from {filename}")
                except Exception as e:
                    logger.error(f"Error formatting chunk {i}: {e}", exc_info=True)
            
            formatted_result = "\n".join(results)
            logger.info(f"Returning {len(formatted_result)} characters to AI")
            return formatted_result
            
    except Exception as e:
        logger.error(f"Error searching documents: {e}", exc_info=True)
        return f"Error searching documents: {str(e)}"

@tool
async def search_user_documents(query: str, config: Optional[RunnableConfig] = None) -> str:
    """
    Search through user's uploaded documents using semantic similarity.
    
    **IMPORTANT**: ALWAYS use this tool when:
    - User uploads a file and asks about it
    - User asks "what is this file?" or "explain this file"
    - User mentions "my document", "this PDF", "uploaded file"
    - User asks questions about content that might be in their files
    
    Examples:
    - "What does my PDF say about X?"
    - "Explain this file"
    - "Summarize the document I uploaded"
    - "What's in my files about Z?"
    
    Args:
        query: What to search for in the documents
    
    Returns:
        Relevant document excerpts with source filenames
    """
    return await _search_documents_impl(query, config, limit=5)

def get_document_tools():
    """Get all document-related tools"""
    return [search_user_documents]
