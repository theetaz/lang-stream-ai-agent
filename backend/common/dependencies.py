"""
FastAPI dependencies for authentication and database access.
"""
from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from database.async_connection import get_async_db
from auth.jwt import verify_token
from database.crud.user_crud import get_user_by_id
from database.crud.session_crud import get_session_by_id, update_session_activity


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Dependency to get current user from JWT token and validate session."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")

    token = auth_header.replace("Bearer ", "")
    payload = verify_token(token, token_type="access")

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("user_id")
    session_id = payload.get("session_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    # Check session validity if session_id exists
    if session_id:
        session = await get_session_by_id(db, session_id)
        if not session or not session.is_active:
            raise HTTPException(status_code=401, detail="Session expired or invalid")
        
        # Update session activity
        await update_session_activity(db, session_id)

    user = await get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return user

