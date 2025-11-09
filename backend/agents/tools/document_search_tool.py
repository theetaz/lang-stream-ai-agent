from typing import Optional
from uuid import UUID
from langchain_core.tools import tool
from langchain_core.runnables.config import RunnableConfig
from common.logger import get_logger

logger = get_logger(__name__)

async def _search_documents_impl(query: str, config: Optional[RunnableConfig] = None, limit: int = 5) -> str:
    """Internal implementation of document search"""
    try:
        from database.db_client import AsyncSessionLocal
        from api.v1.chat.rag_service import rag_service
        
        # Extract user_id and session_id from config
        user_id = None
        session_id = None
        
        logger.info(f"Tool config: {config}")
        
        if config and "configurable" in config:
            user_id_str = config["configurable"].get("user_id")
            session_id_str = config["configurable"].get("thread_id")
            
            logger.info(f"Extracted from config - user_id_str: {user_id_str}, session_id_str: {session_id_str}")
            
            if user_id_str:
                try:
                    user_id = UUID(user_id_str)
                except (ValueError, TypeError):
                    logger.error(f"Failed to convert user_id_str to UUID: {user_id_str}")
                    pass
            
            if session_id_str:
                try:
                    session_id = UUID(session_id_str)
                except (ValueError, TypeError):
                    logger.error(f"Failed to convert session_id_str to UUID: {session_id_str}")
                    pass
        
        if not user_id:
            logger.error("User context not available from config")
            return "Unable to search documents: User context not available."
        
        logger.info(f"🔍 Document search - user_id: {user_id}, session_id: {session_id}, query: '{query}'")
        
        async with AsyncSessionLocal() as db:
            chunks = await rag_service.search_documents(
                db=db,
                user_id=user_id,
                query=query,
                session_id=session_id,
                limit=limit
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
