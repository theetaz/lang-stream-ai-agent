"""
Async CRUD operations for Session model.
Handles session creation, retrieval, and management.
"""
import hashlib
from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.session import Session


def hash_refresh_token(token: str) -> str:
    """Hash a refresh token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


async def create_session(
    db: AsyncSession,
    session_id: str,
    user_id: int,
    refresh_token: str,
    device_info: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Session:
    """
    Create a new session in the database.
    
    Args:
        db: Async database session
        session_id: Unique session identifier (UUID)
        user_id: User ID
        refresh_token: Refresh token (will be hashed)
        device_info: Device/browser information
        ip_address: IP address
        user_agent: User agent string
        
    Returns:
        The created Session object
    """
    refresh_token_hash = hash_refresh_token(refresh_token)
    
    session = Session(
        id=session_id,
        user_id=user_id,
        refresh_token_hash=refresh_token_hash,
        device_info=device_info,
        ip_address=ip_address,
        user_agent=user_agent,
        is_active=True,
    )
    
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    return session


async def get_session_by_id(db: AsyncSession, session_id: str) -> Optional[Session]:
    """
    Get a session by its ID.
    
    Args:
        db: Async database session
        session_id: Session ID
        
    Returns:
        Session object if found, None otherwise
    """
    result = await db.execute(select(Session).where(Session.id == session_id))
    return result.scalars().first()


async def get_session_by_refresh_token(db: AsyncSession, refresh_token: str) -> Optional[Session]:
    """
    Get a session by refresh token hash.
    
    Args:
        db: Async database session
        refresh_token: Refresh token
        
    Returns:
        Session object if found, None otherwise
    """
    refresh_token_hash = hash_refresh_token(refresh_token)
    result = await db.execute(
        select(Session).where(Session.refresh_token_hash == refresh_token_hash)
    )
    return result.scalars().first()


async def get_user_sessions(
    db: AsyncSession,
    user_id: int,
    active_only: bool = True,
) -> List[Session]:
    """
    Get all sessions for a user.
    
    Args:
        db: Async database session
        user_id: User ID
        active_only: If True, only return active sessions
        
    Returns:
        List of Session objects
    """
    query = select(Session).where(Session.user_id == user_id)
    
    if active_only:
        query = query.where(Session.is_active == True)
    
    query = query.order_by(Session.updated_at.desc())
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def deactivate_session(db: AsyncSession, session_id: str) -> Optional[Session]:
    """
    Deactivate a session (logout).
    
    Args:
        db: Async database session
        session_id: Session ID
        
    Returns:
        Updated Session object if found, None otherwise
    """
    session = await get_session_by_id(db, session_id)
    
    if not session:
        return None
    
    session.is_active = False
    await db.commit()
    await db.refresh(session)
    
    return session


async def deactivate_all_user_sessions(db: AsyncSession, user_id: int) -> int:
    """
    Deactivate all sessions for a user (logout from all devices).
    
    Args:
        db: Async database session
        user_id: User ID
        
    Returns:
        Number of sessions deactivated
    """
    sessions = await get_user_sessions(db, user_id, active_only=True)
    
    for session in sessions:
        session.is_active = False
    
    await db.commit()
    return len(sessions)


async def update_session_activity(db: AsyncSession, session_id: str) -> Optional[Session]:
    """
    Update session's last activity timestamp.
    
    Args:
        db: Async database session
        session_id: Session ID
        
    Returns:
        Updated Session object if found, None otherwise
    """
    session = await get_session_by_id(db, session_id)
    
    if not session:
        return None
    
    # TimestampMixin will automatically update updated_at
    await db.commit()
    await db.refresh(session)
    
    return session


async def delete_session(db: AsyncSession, session_id: str) -> bool:
    """
    Delete a session permanently.
    
    Args:
        db: Async database session
        session_id: Session ID
        
    Returns:
        True if session was deleted, False if not found
    """
    session = await get_session_by_id(db, session_id)
    
    if not session:
        return False
    
    await db.delete(session)
    await db.commit()
    
    return True

