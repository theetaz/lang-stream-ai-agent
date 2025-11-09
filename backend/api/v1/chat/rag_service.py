from uuid import UUID
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from models.file_chunk import FileChunk
from models.uploaded_file import UploadedFile, ProcessingStatus
from common.embedding_service import embedding_service
from common.logger import get_logger

logger = get_logger(__name__)

class RAGService:
    async def search_documents(
        self,
        db: AsyncSession,
        user_id: UUID,
        query: str,
        session_id: Optional[UUID] = None,
        limit: int = 5,
        search_all_sessions: bool = True  # Search across all user sessions by default
    ) -> List[FileChunk]:
        """
        Search documents using semantic similarity.
        
        Args:
            db: Database session
            user_id: User ID to search documents for
            query: Search query
            session_id: Optional session ID to filter by (if None and search_all_sessions=True, searches all sessions)
            limit: Maximum number of results
            search_all_sessions: If True, search across all user sessions; if False, only current session
        
        Returns:
            List of relevant FileChunk objects ordered by relevance
        """
        logger.info(f"Searching documents for user {user_id}, session {session_id}, query: '{query}', search_all_sessions={search_all_sessions}")
        
        query_embedding = await embedding_service.generate_embedding(query)
        
        # Base query: search all completed files for this user
        sql = select(FileChunk).join(UploadedFile).where(
            UploadedFile.user_id == user_id,
            UploadedFile.processing_status == ProcessingStatus.COMPLETED
        ).options(selectinload(FileChunk.file))
        
        # Only filter by session if explicitly requested and search_all_sessions is False
        if session_id and not search_all_sessions:
            logger.info(f"Filtering by session_id: {session_id}")
            sql = sql.where(UploadedFile.session_id == session_id)
        elif search_all_sessions:
            logger.info(f"Searching across ALL user sessions (not filtering by session_id)")
        
        # Order by cosine similarity (lower distance = more similar)
        sql = sql.order_by(
            FileChunk.embedding.cosine_distance(query_embedding)
        ).limit(limit)
        
        result = await db.execute(sql)
        chunks = result.scalars().all()
        
        if chunks:
            logger.info(f"✅ Found {len(chunks)} relevant chunks for query: '{query[:50]}...'")
            for i, chunk in enumerate(chunks, 1):
                session_info = f"session {chunk.file.session_id}" if chunk.file else "unknown session"
                logger.info(f"  Chunk {i}: {chunk.file.filename if chunk.file else 'No file'} from {session_info} (index {chunk.chunk_index})")
        else:
            logger.warning(f"❌ No chunks found for user {user_id}, query: '{query}'")
            
            # Debug: Check if files exist at all
            debug_sql = select(UploadedFile).where(
                UploadedFile.user_id == user_id,
                UploadedFile.processing_status == ProcessingStatus.COMPLETED
            )
            debug_result = await db.execute(debug_sql)
            debug_files = debug_result.scalars().all()
            logger.info(f"  Debug: Found {len(debug_files)} completed files for this user")
            for f in debug_files:
                logger.info(f"    File: {f.filename}, ID: {f.id}, Session: {f.session_id}")
        
        return list(chunks)
    
    def format_context(self, chunks: List[FileChunk]) -> str:
        if not chunks:
            return "No relevant information found in your documents."
        
        context = []
        for chunk in chunks:
            context.append(
                f"Source: {chunk.file.filename}\n"
                f"Content: {chunk.content}\n"
            )
        return "\n---\n".join(context)

rag_service = RAGService()

