"""
Authentication API endpoints with JWT tokens.
Supports both Google OAuth (SSO) and email/password authentication.
Frontend handles OAuth callback, backend creates user and issues JWT tokens.
Includes session management for multi-device support.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from user_agents import parse as parse_user_agent

from auth.jwt import create_access_token, create_refresh_token, verify_token
from database import get_async_db
from database.crud import (
    get_or_create_user_by_google,
    get_user_by_email,
    create_user,
    get_user_by_id,
    create_session,
    get_session_by_id,
    get_session_by_refresh_token,
    get_user_sessions,
    deactivate_session,
    deactivate_all_user_sessions,
    update_session_activity,
)

router = APIRouter(prefix="/auth", tags=["authentication"])

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============= Request/Response Models =============

class GoogleAuthRequest(BaseModel):
    """Request from frontend after Google OAuth success"""
    google_id: str
    email: EmailStr
    name: str | None = None
    avatar_url: str | None = None


class EmailPasswordRegisterRequest(BaseModel):
    """Request for email/password registration"""
    email: EmailStr
    password: str
    name: str | None = None


class EmailPasswordLoginRequest(BaseModel):
    """Request for email/password login"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict
    session_id: str


class RefreshRequest(BaseModel):
    """Request to refresh access token"""
    refresh_token: str


class UserResponse(BaseModel):
    """User info response"""
    id: int
    email: str
    name: str | None
    avatar_url: str | None
    is_active: bool


# ============= Helper Functions =============

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_device_info(user_agent: str | None) -> str | None:
    """Extract device info from user agent string."""
    if not user_agent:
        return None
    
    try:
        ua = parse_user_agent(user_agent)
        device = ua.device.family if ua.device.family != "Other" else None
        os = f"{ua.os.family} {ua.os.version_string}".strip() if ua.os.family != "Other" else None
        browser = f"{ua.browser.family} {ua.browser.version_string}".strip() if ua.browser.family != "Other" else None
        
        parts = [p for p in [device, os, browser] if p]
        return ", ".join(parts) if parts else None
    except Exception:
        return None


async def create_token_response(
    user,
    request: Request,
    db: AsyncSession,
    existing_session_id: str | None = None,
) -> dict:
    """Create JWT tokens, create/update session, and format response"""
    # Extract request info
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
    device_info = get_device_info(user_agent)
    
    # Use existing session ID if refreshing, otherwise create new
    session_id = existing_session_id or str(uuid.uuid4())
    
    # Create tokens with session_id
    token_data = {
        "user_id": user.id,
        "email": user.email,
        "name": user.name,
        "session_id": session_id,
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"user_id": user.id, "session_id": session_id})
    
    # Create or update session
    if existing_session_id:
        # Update existing session activity
        from database.crud import update_session_activity
        await update_session_activity(db, existing_session_id)
    else:
        # Create new session
        await create_session(
            db=db,
            session_id=session_id,
            user_id=user.id,
            refresh_token=refresh_token,
            device_info=device_info,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user.to_dict(),
        "session_id": session_id,
    }


async def get_current_user(request: Request, db: AsyncSession = Depends(get_async_db)):
    """Dependency to get current user from JWT token and validate session"""
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


# ============= SSO (Google OAuth) Endpoints =============

@router.post("/google", response_model=TokenResponse)
async def google_auth(
    auth_data: GoogleAuthRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Handle Google OAuth login/registration.
    Frontend sends user data after successful OAuth, backend creates user and returns JWT.

    Flow:
    1. Frontend handles Google OAuth and gets user info
    2. Frontend sends user info to this endpoint
    3. Backend creates/gets user in database
    4. Backend creates session and returns JWT tokens
    """
    try:
        # Get or create user
        user, created = await get_or_create_user_by_google(
            db=db,
            google_id=auth_data.google_id,
            email=auth_data.email,
            name=auth_data.name,
            avatar_url=auth_data.avatar_url,
        )

        # Create and return JWT tokens with session
        return await create_token_response(user, request, db)

    except Exception as e:
        print(f"Google auth error: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")


# ============= Email/Password Endpoints =============

@router.post("/register", response_model=TokenResponse)
async def register(
    data: EmailPasswordRegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Register a new user with email and password.

    Args:
        data: Email, password, and optional name

    Returns:
        JWT tokens, user info, and session_id
    """
    # Check if user already exists
    existing_user = await get_user_by_email(db, data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash password
    hashed_password = hash_password(data.password)

    # Create user
    user = await create_user(
        db=db,
        email=data.email,
        password_hash=hashed_password,
        name=data.name,
    )

    return await create_token_response(user, request, db)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: EmailPasswordLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Login with email and password.

    Args:
        data: Email and password

    Returns:
        JWT tokens, user info, and session_id
    """
    # Get user
    user = await get_user_by_email(db, data.email)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Verify password
    if not user.password_hash or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account is inactive")

    return await create_token_response(user, request, db)


# ============= Token Management Endpoints =============

@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    data: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Refresh access token using refresh token.

    Args:
        data: Refresh token

    Returns:
        New JWT tokens with same session_id
    """
    # Verify refresh token
    payload = verify_token(data.refresh_token, token_type="refresh")

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("user_id")
    session_id = payload.get("session_id")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    # Check session validity
    if session_id:
        session = await get_session_by_refresh_token(db, data.refresh_token)
        if not session or not session.is_active:
            raise HTTPException(status_code=401, detail="Session expired or invalid")

    # Get user
    user = await get_user_by_id(db, user_id)

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # Create new tokens with same session_id
    return await create_token_response(user, request, db, existing_session_id=session_id)


@router.post("/logout")
async def logout(
    request: Request,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Logout endpoint - deactivates current session.
    Client should remove tokens from storage.
    """
    # Get session_id from token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
        payload = verify_token(token, token_type="access")
        if payload:
            session_id = payload.get("session_id")
            if session_id:
                await deactivate_session(db, session_id)
    
    return {"message": "Logged out successfully"}


# ============= User Info Endpoint =============

@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user = Depends(get_current_user)
):
    """
    Get current user info from JWT token.

    Requires: Authorization header with Bearer token

    Returns:
        Current user info
    """
    return current_user


# ============= Session Management Endpoints =============

class SessionResponse(BaseModel):
    """Session info response"""
    id: str
    device_info: str | None
    ip_address: str | None
    user_agent: str | None
    is_active: bool
    created_at: str
    updated_at: str
    last_activity: str


class SessionsListResponse(BaseModel):
    """List of sessions response"""
    sessions: list[SessionResponse]


@router.get("/sessions", response_model=SessionsListResponse)
async def get_sessions(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get all active sessions for the current user.
    
    Returns:
        List of all sessions (active and inactive)
    """
    sessions = await get_user_sessions(db, current_user.id, active_only=False)
    
    return {
        "sessions": [SessionResponse(**session.to_dict()) for session in sessions]
    }


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete a specific session by session_id.
    User can only delete their own sessions.
    
    Args:
        session_id: Session ID to delete
        
    Returns:
        Success message
    """
    session = await get_session_by_id(db, session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot delete other user's session")
    
    await deactivate_session(db, session_id)
    
    return {"message": "Session deleted successfully"}


@router.delete("/sessions/all")
async def delete_all_sessions(
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete all sessions for the current user (logout from all devices).
    
    Note: This endpoint extracts user_id directly from the token without
    validating the session, since we're deleting all sessions anyway.
    
    Returns:
        Success message with count of deleted sessions
    """
    # Extract user_id from token without session validation
    # This allows deleting all sessions even if current session is invalid
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization token")
    
    token = auth_header.replace("Bearer ", "")
    payload = verify_token(token, token_type="access")
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    # Verify user exists and is active
    user = await get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    # Deactivate all sessions for this user
    count = await deactivate_all_user_sessions(db, user_id)
    
    return {"message": f"Logged out from {count} session(s)"}
