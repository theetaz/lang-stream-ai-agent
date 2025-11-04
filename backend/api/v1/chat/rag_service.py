from uuid import UUID
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.file_chunk import FileChunk
from models.uploaded_file import UploadedFile, ProcessingStatus
from common.embedding_service import embedding_service
from common.logger import get_logger

logger = get_logger(__name__)

class RAGService:
    async def search_documents(
        self,
        db: AsyncSession,
        user_id: int,
        query: str,
        session_id: Optional[UUID] = None,
        limit: int = 5
    ) -> List[FileChunk]:
        query_embedding = await embedding_service.generate_embedding(query)
        
        sql = select(FileChunk).join(UploadedFile).where(
            UploadedFile.user_id == user_id,
            UploadedFile.processing_status == ProcessingStatus.COMPLETED
        )
        
        if session_id:
            sql = sql.where(UploadedFile.session_id == session_id)
        
        sql = sql.order_by(
            FileChunk.embedding.cosine_distance(query_embedding)
        ).limit(limit)
        
        result = await db.execute(sql)
        chunks = result.scalars().all()
        
        logger.info(f"Found {len(chunks)} relevant chunks for query: {query[:50]}...")
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

