from uuid import UUID
from openai import AsyncOpenAI
from config.settings import settings
from sqlalchemy.ext.asyncio import AsyncSession
from api.v1.chat.message_service import message_service
from api.v1.chat.session_service import session_service
from common.logger import get_logger

logger = get_logger(__name__)

class TitleGenerator:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def generate_title(self, db: AsyncSession, session_id: UUID, user_id: int) -> str:
        messages = await message_service.get_messages(db, session_id, limit=5)
        
        if not messages:
            return "New Chat"
        
        conversation = "\n".join([
            f"{msg.role.value}: {msg.content[:200]}" 
            for msg in messages
        ])
        
        prompt = f"""Generate a short title (3-5 words) for this conversation:

{conversation}

Title:"""
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=20,
                temperature=0.7
            )
            
            title = response.choices[0].message.content.strip()
            title = title.strip('"\'')
            
            await session_service.update_title(db, session_id, user_id, title)
            logger.info(f"Generated title for session {session_id}: {title}")
            
            return title
        except Exception as e:
            logger.error(f"Failed to generate title: {e}")
            return "New Chat"

title_generator = TitleGenerator()

