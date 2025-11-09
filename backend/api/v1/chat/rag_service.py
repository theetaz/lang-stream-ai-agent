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
        limit: int = 5
    ) -> List[FileChunk]:
        logger.info(f"Searching documents for user {user_id}, session {session_id}, query: '{query}'")
        
        query_embedding = await embedding_service.generate_embedding(query)
        
        sql = select(FileChunk).join(UploadedFile).where(
            UploadedFile.user_id == user_id,
            UploadedFile.processing_status == ProcessingStatus.COMPLETED
        ).options(selectinload(FileChunk.file))
        
        if session_id:
            logger.info(f"Filtering by session_id: {session_id}")
            sql = sql.where(UploadedFile.session_id == session_id)
        
        sql = sql.order_by(
            FileChunk.embedding.cosine_distance(query_embedding)
        ).limit(limit)
        
        result = await db.execute(sql)
        chunks = result.scalars().all()
        
        if chunks:
            logger.info(f"✅ Found {len(chunks)} relevant chunks for query: {query[:50]}...")
            for i, chunk in enumerate(chunks, 1):
                logger.info(f"  Chunk {i}: {chunk.file.filename if chunk.file else 'No file'} (index {chunk.chunk_index})")
        else:
            logger.warning(f"❌ No chunks found for user {user_id}, session {session_id}, query: '{query}'")
            
            # Debug: Check if files exist at all
            debug_sql = select(UploadedFile).where(
                UploadedFile.user_id == user_id,
                UploadedFile.processing_status == ProcessingStatus.COMPLETED
            )
            if session_id:
                debug_sql = debug_sql.where(UploadedFile.session_id == session_id)
            
            debug_result = await db.execute(debug_sql)
            debug_files = debug_result.scalars().all()
            logger.info(f"  Debug: Found {len(debug_files)} completed files for this user/session")
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

