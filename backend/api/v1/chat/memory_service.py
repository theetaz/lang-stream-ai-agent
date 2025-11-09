from uuid import UUID
from typing import Literal, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from common.embedding_service import embedding_service
from common.logger import get_logger
from datetime import datetime

logger = get_logger(__name__)

class MemoryItem:
    def __init__(self, namespace: tuple, key: str, value: dict, embedding: Optional[list[float]] = None):
        self.namespace = namespace
        self.key = key
        self.value = value
        self.embedding = embedding

class MemoryService:
    async def save_semantic_memory(
        self,
        db: AsyncSession,
        user_id: UUID,
        memory_id: str,
        content: str,
        memory_type: Literal["fact", "preference", "context", "relationship"],
        metadata: Optional[dict] = None
    ):
        embedding = await embedding_service.generate_embedding(content)
        
        memory_data = {
            "content": content,
            "memory_type": memory_type,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
            "embedding": embedding
        }
        
        logger.info(f"Saved semantic memory for user {user_id}: {memory_id}")
        return memory_data
    
    async def search_semantic_memories(
        self,
        db: AsyncSession,
        user_id: UUID,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 5
    ) -> list[dict]:
        query_embedding = await embedding_service.generate_embedding(query)
        
        logger.info(f"Searching semantic memories for user {user_id} with query: {query}")
        return []
    
    async def get_all_memories(self, db: AsyncSession, user_id: UUID) -> list[dict]:
        logger.info(f"Fetching all memories for user {user_id}")
        return []
    
    async def delete_memory(
        self, 
        db: AsyncSession, 
        user_id: UUID, 
        memory_type: str, 
        memory_id: str
    ):
        logger.info(f"Deleted memory {memory_id} for user {user_id}")

memory_service = MemoryService()

