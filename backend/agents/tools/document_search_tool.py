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
        
        if config and "configurable" in config:
            user_id_str = config["configurable"].get("user_id")
            session_id_str = config["configurable"].get("thread_id")
            
            if user_id_str:
                try:
                    user_id = int(user_id_str)
                except (ValueError, TypeError):
                    pass
            
            if session_id_str:
                try:
                    session_id = UUID(session_id_str)
                except (ValueError, TypeError):
                    pass
        
        if not user_id:
            return "Unable to search documents: User context not available."
        
        logger.info(f"Searching documents for user {user_id}: {query}")
        
        async with AsyncSessionLocal() as db:
            chunks = await rag_service.search_documents(
                db=db,
                user_id=user_id,
                query=query,
                session_id=session_id,
                limit=limit
            )
            
            if not chunks:
                return "No relevant information found in your uploaded documents. Try uploading files first, then ask me about them once they're processed."
            
            # Format results nicely
            results = []
            results.append(f"Found {len(chunks)} relevant excerpts from your documents:\n")
            
            for i, chunk in enumerate(chunks, 1):
                filename = chunk.file.filename if chunk.file else "Unknown file"
                content = chunk.content[:400]  # Limit content length
                if len(chunk.content) > 400:
                    content += "..."
                
                results.append(f"\n📄 Source {i}: {filename}")
                results.append(f"{content}\n")
            
            return "\n".join(results)
            
    except Exception as e:
        logger.error(f"Error searching documents: {e}", exc_info=True)
        return f"Error searching documents: {str(e)}"

@tool
async def search_user_documents(query: str, config: Optional[RunnableConfig] = None) -> str:
    """
    Search through user's uploaded documents using semantic similarity.
    
    Use this tool when the user asks about their uploaded documents or files:
    - "What does my PDF say about X?"
    - "Find information about Y in my uploaded files"
    - "Summarize the document I uploaded"
    - "What's in my documents about Z?"
    
    Args:
        query: What to search for in the documents
    
    Returns:
        Relevant document excerpts with source filenames
    """
    return await _search_documents_impl(query, config, limit=5)

def get_document_tools():
    """Get all document-related tools"""
    return [search_user_documents]
