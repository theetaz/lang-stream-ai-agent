from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, desc
from sqlalchemy.sql import func
from models.chat_session import ChatSession
from models.chat_message import ChatMessage
from common.logger import get_logger
from common.errors import NotFoundError, ForbiddenError
from datetime import datetime

logger = get_logger(__name__)

class SessionService:
    async def create_session(
        self,
        db: AsyncSession,
        user_id: int,
        title: Optional[str] = None
    ) -> ChatSession:
        session = ChatSession(
            user_id=user_id,
            title=title or "New Chat",
            is_archived=False
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        
        logger.info(f"Created chat session {session.id} for user {user_id}")
        return session
    
    async def get_sessions(
        self,
        db: AsyncSession,
        user_id: int,
        archived: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> list[ChatSession]:
        query = select(ChatSession).where(
            ChatSession.user_id == user_id,
            ChatSession.is_archived == archived
        ).order_by(desc(ChatSession.last_message_at), desc(ChatSession.created_at)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        sessions = result.scalars().all()
        
        logger.info(f"Fetched {len(sessions)} sessions for user {user_id}")
        return list(sessions)
    
    async def get_session(
        self,
        db: AsyncSession,
        session_id: UUID,
        user_id: int
    ) -> ChatSession:
        query = select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        )
        result = await db.execute(query)
        session = result.scalar_one_or_none()
        
        if not session:
            raise NotFoundError(f"Session {session_id} not found")
        
        return session
    
    async def update_title(
        self,
        db: AsyncSession,
        session_id: UUID,
        user_id: int,
        title: str
    ) -> ChatSession:
        session = await self.get_session(db, session_id, user_id)
        session.title = title
        await db.commit()
        await db.refresh(session)
        
        logger.info(f"Updated title for session {session_id}")
        return session
    
    async def update_last_message_at(
        self,
        db: AsyncSession,
        session_id: UUID
    ):
        await db.execute(
            update(ChatSession)
            .where(ChatSession.id == session_id)
            .values(last_message_at=datetime.utcnow())
        )
        await db.commit()
    
    async def archive_session(
        self,
        db: AsyncSession,
        session_id: UUID,
        user_id: int
    ) -> ChatSession:
        session = await self.get_session(db, session_id, user_id)
        session.is_archived = True
        await db.commit()
        await db.refresh(session)
        
        logger.info(f"Archived session {session_id}")
        return session
    
    async def delete_session(
        self,
        db: AsyncSession,
        session_id: UUID,
        user_id: int
    ):
        session = await self.get_session(db, session_id, user_id)
        await db.delete(session)
        await db.commit()
        
        logger.info(f"Deleted session {session_id}")

session_service = SessionService()

