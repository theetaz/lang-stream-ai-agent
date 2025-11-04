from langchain_core.tools import tool
from common.logger import get_logger

logger = get_logger(__name__)

@tool
async def search_user_documents(query: str, limit: int = 5) -> str:
    """
    Search through user's uploaded documents.
    
    Use when user asks about their documents:
    - "What does my contract say about X?"
    - "Find information about Y in my files"
    - "Summarize the PDF I uploaded"
    
    Args:
        query: What to search for
        limit: Maximum number of results (default: 5)
    
    Returns:
        Relevant document excerpts
    """
    logger.info(f"Tool called: search_user_documents - query: {query}")
    
    return "No documents have been uploaded yet. Please upload documents first."

def get_document_tools():
    """Get all document-related tools"""
    return [search_user_documents]

