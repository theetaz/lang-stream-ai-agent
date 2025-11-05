from api.v1.auth.service import AuthService
from auth.utils import get_current_user
from common.response import APIResponse, success_response
from database.db_client import get_db
from fastapi import APIRouter, Depends, Request
from schemas.auth import (
    EmailPasswordLoginRequest,
    EmailPasswordRegisterRequest,
    GoogleAuthRequest,
    RefreshRequest,
    SessionsListResponse,
    TokenResponse,
    UserResponse,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/auth", tags=["authentication"])


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Dependency to get AuthService instance."""
    return AuthService(db)


# ============= SSO (Google OAuth) Endpoints =============
@router.post("/google", response_model=APIResponse[TokenResponse])
async def google_auth(
    auth_data: GoogleAuthRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service),
):
    """Handle Google OAuth login/registration."""
    result = await service.google_auth(auth_data, request)
    return success_response(result, message="Authentication successful")


# ============= Email/Password Endpoints =============
@router.post("/register", response_model=APIResponse[TokenResponse])
async def register(
    data: EmailPasswordRegisterRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service),
):
    """Register a new user with email and password."""
    result = await service.register(data, request)
    return success_response(result, message="User registered successfully")


@router.post("/login", response_model=APIResponse[TokenResponse])
async def login(
    data: EmailPasswordLoginRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service),
):
    """Login with email and password."""
    result = await service.login(data, request)
    return success_response(result, message="Login successful")


# ============= Token Management Endpoints =============
@router.post("/refresh", response_model=APIResponse[TokenResponse])
async def refresh_tokens(
    data: RefreshRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service),
):
    """Refresh access token using refresh token."""
    result = await service.refresh_tokens(data, request)
    return success_response(result, message="Token refreshed successfully")


@router.post("/logout", response_model=APIResponse[dict])
async def logout(
    request: Request,
    current_user=Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    """Logout endpoint - deactivates current session."""
    result = await service.logout(request, current_user.id)
    return success_response(result, message="Logout successful")


# ============= User Info Endpoint =============
@router.get("/me", response_model=APIResponse[UserResponse])
async def get_me(current_user=Depends(get_current_user)):
    """Get current user info from JWT token."""
    return success_response(
        current_user.to_dict(), message="User info retrieved successfully"
    )


# ============= Session Management Endpoints =============
@router.get("/sessions", response_model=APIResponse[SessionsListResponse])
async def get_sessions(
    is_active: bool | None = None,
    limit: int = 50,
    offset: int = 0,
    current_user=Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    if limit > 100:
        limit = 100
    if limit < 1:
        limit = 1

    result = await service.get_sessions(
        user_id=current_user.id, is_active=is_active, limit=limit, offset=offset
    )
    return success_response(result, message="Sessions retrieved successfully")


@router.delete("/sessions/all", response_model=APIResponse[dict])
async def delete_all_sessions(
    current_user=Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    """Delete all sessions for the current user (logout from all devices)."""
    result = await service.delete_all_sessions(current_user.id)
    return success_response(result, message="All sessions deleted successfully")


@router.delete("/sessions/{session_id}", response_model=APIResponse[dict])
async def delete_session(
    session_id: str,
    current_user=Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    """Delete a specific session by session_id."""
    result = await service.delete_session(session_id, current_user.id)
    return success_response(result, message="Session deleted successfully")
