"""
Authentication API routes.
Only HTTP handling and service calls. No business logic.
"""
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database.db_client import get_db
from api.v1.auth.service import AuthService
from auth.utils import get_current_user
from schemas.auth import (
    GoogleAuthRequest,
    EmailPasswordRegisterRequest,
    EmailPasswordLoginRequest,
    TokenResponse,
    RefreshRequest,
    UserResponse,
    SessionsListResponse,
)


router = APIRouter(prefix="/auth", tags=["authentication"])


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Dependency to get AuthService instance."""
    return AuthService(db)


# ============= SSO (Google OAuth) Endpoints =============

@router.post("/google", response_model=TokenResponse)
async def google_auth(
    auth_data: GoogleAuthRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service),
):
    """Handle Google OAuth login/registration."""
    return await service.google_auth(auth_data, request)


# ============= Email/Password Endpoints =============

@router.post("/register", response_model=TokenResponse)
async def register(
    data: EmailPasswordRegisterRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service),
):
    """Register a new user with email and password."""
    return await service.register(data, request)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: EmailPasswordLoginRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service),
):
    """Login with email and password."""
    return await service.login(data, request)


# ============= Token Management Endpoints =============

@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    data: RefreshRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service),
):
    """Refresh access token using refresh token."""
    return await service.refresh_tokens(data, request)


@router.post("/logout")
async def logout(
    request: Request,
    service: AuthService = Depends(get_auth_service),
):
    """Logout endpoint - deactivates current session."""
    return await service.logout(request)


# ============= User Info Endpoint =============

@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user = Depends(get_current_user)
):
    """Get current user info from JWT token."""
    return current_user


# ============= Session Management Endpoints =============

@router.get("/sessions", response_model=SessionsListResponse)
async def get_sessions(
    current_user = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    """Get all active sessions for the current user."""
    return await service.get_sessions(current_user.id)


@router.delete("/sessions/all")
async def delete_all_sessions(
    request: Request,
    service: AuthService = Depends(get_auth_service),
):
    """Delete all sessions for the current user (logout from all devices)."""
    # Extract user_id from token without session validation
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
    user = await get_user_by_id(service.db, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return await service.delete_all_sessions(user_id)


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    """Delete a specific session by session_id."""
    return await service.delete_session(session_id, current_user.id)

