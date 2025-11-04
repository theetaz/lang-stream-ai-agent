from openai import AsyncOpenAI
from config.settings import settings
from common.logger import get_logger

logger = get_logger(__name__)

class EmbeddingService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "text-embedding-3-small"
        self.dimensions = 1536
    
    async def generate_embedding(self, text: str) -> list[float]:
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    async def batch_embeddings(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise

embedding_service = EmbeddingService()

