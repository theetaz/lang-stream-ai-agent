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
        user_id: UUID,
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
        user_id: UUID,
        archived: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[list[ChatSession], int]:
        # Count total sessions
        count_query = select(func.count(ChatSession.id)).where(
            ChatSession.user_id == user_id,
            ChatSession.is_archived == archived
        )
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        # Get sessions ordered by pinned first, then by last_message_at
        query = select(ChatSession).where(
            ChatSession.user_id == user_id,
            ChatSession.is_archived == archived
        ).order_by(
            desc(ChatSession.is_pinned),  # Pinned sessions first
            desc(ChatSession.last_message_at),
            desc(ChatSession.created_at)
        ).limit(limit).offset(offset)
        
        result = await db.execute(query)
        sessions = result.scalars().all()
        
        logger.info(f"Fetched {len(sessions)} sessions (total: {total}) for user {user_id}")
        return list(sessions), total
    
    async def get_session(
        self,
        db: AsyncSession,
        session_id: UUID,
        user_id: UUID
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
    
    async def update_session(
        self,
        db: AsyncSession,
        session_id: UUID,
        user_id: UUID,
        title: Optional[str] = None,
        is_archived: Optional[bool] = None,
        is_pinned: Optional[bool] = None
    ) -> ChatSession:
        session = await self.get_session(db, session_id, user_id)
        
        if title is not None:
            session.title = title
        if is_archived is not None:
            session.is_archived = is_archived
        if is_pinned is not None:
            session.is_pinned = is_pinned
        
        await db.commit()
        await db.refresh(session)
        
        logger.info(f"Updated session {session_id}")
        return session
    
    async def update_title(
        self,
        db: AsyncSession,
        session_id: UUID,
        user_id: UUID,
        title: str
    ) -> ChatSession:
        return await self.update_session(db, session_id, user_id, title=title)
    
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
        user_id: UUID
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
        user_id: UUID
    ):
        from models.uploaded_file import UploadedFile
        
        session = await self.get_session(db, session_id, user_id)
        
        # Delete related files first to avoid foreign key constraint issues
        # SQLAlchemy tries to set session_id to NULL before CASCADE delete
        files_query = select(UploadedFile).where(UploadedFile.session_id == session_id)
        files_result = await db.execute(files_query)
        files = files_result.scalars().all()
        
        for file in files:
            await db.delete(file)
        
        # Now delete the session
        await db.delete(session)
        await db.commit()
        
        logger.info(f"Deleted session {session_id} and {len(files)} associated files")

session_service = SessionService()

