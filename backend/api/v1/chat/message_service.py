from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from models.chat_message import ChatMessage, MessageRole
from common.logger import get_logger

logger = get_logger(__name__)

class MessageService:
    async def save_message(
        self,
        db: AsyncSession,
        session_id: UUID,
        role: MessageRole,
        content: str,
        meta: Optional[dict] = None
    ) -> ChatMessage:
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            meta=meta
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)
        
        logger.info(f"Saved {role.value} message to session {session_id}")
        return message
    
    async def get_messages(
        self,
        db: AsyncSession,
        session_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> list[ChatMessage]:
        query = select(ChatMessage).where(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at).limit(limit).offset(offset)
        
        result = await db.execute(query)
        messages = result.scalars().all()
        
        logger.info(f"Fetched {len(messages)} messages for session {session_id}")
        return list(messages)
    
    async def get_last_n_messages(
        self,
        db: AsyncSession,
        session_id: UUID,
        n: int = 20
    ) -> list[ChatMessage]:
        query = select(ChatMessage).where(
            ChatMessage.session_id == session_id
        ).order_by(desc(ChatMessage.created_at)).limit(n)
        
        result = await db.execute(query)
        messages = result.scalars().all()
        
        return list(reversed(messages))
    
    async def count_messages(
        self,
        db: AsyncSession,
        session_id: UUID
    ) -> int:
        from sqlalchemy import func
        
        query = select(func.count(ChatMessage.id)).where(
            ChatMessage.session_id == session_id
        )
        result = await db.execute(query)
        return result.scalar_one()

message_service = MessageService()

