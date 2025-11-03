from auth.jwt import verify_token
from database.db_client import get_db
from database.crud.session_crud import get_session_by_id, update_session_activity
from database.crud.user_crud import get_user_by_id
from fastapi import Depends, HTTPException, Request, status
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from user_agents import parse as parse_user_agent

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_device_info(user_agent: str | None) -> str | None:
    """Extract device info from user agent string."""
    if not user_agent:
        return None

    try:
        ua = parse_user_agent(user_agent)
        device = ua.device.family if ua.device.family != "Other" else None
        os = (
            f"{ua.os.family} {ua.os.version_string}".strip()
            if ua.os.family != "Other"
            else None
        )
        browser = (
            f"{ua.browser.family} {ua.browser.version_string}".strip()
            if ua.browser.family != "Other"
            else None
        )

        parts = [p for p in [device, os, browser] if p]
        return ", ".join(parts) if parts else None
    except Exception:
        return None


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    """Dependency to get current user from JWT token and validate session."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
        )

    token = auth_header.replace("Bearer ", "")
    payload = verify_token(token, token_type="access")

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )

    user_id = payload.get("user_id")
    session_id = payload.get("session_id")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
        )

    # Check session validity if session_id exists
    if session_id:
        session = await get_session_by_id(db, session_id)
        if not session or not session.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or invalid",
            )

        # Update session activity
        await update_session_activity(db, session_id)

    user = await get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user
