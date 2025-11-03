import bcrypt
from auth.jwt import verify_token
from database.db_client import get_db
from fastapi import Depends, HTTPException, Request, status
from models.session import Session
from models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from user_agents import parse as parse_user_agent


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)


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

    if session_id:
        result = await db.execute(select(Session).where(Session.id == session_id))
        session = result.scalars().first()
        if not session or not session.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or invalid",
            )
        await db.commit()
        await db.refresh(session)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user
