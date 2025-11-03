from api.v1.auth.service import AuthService
from auth.jwt import verify_token
from auth.utils import get_current_user
from common.errors import UnauthorizedError
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
    service: AuthService = Depends(get_auth_service),
):
    """Logout endpoint - deactivates current session."""
    result = await service.logout(request)
    return success_response(result, message="Logout successful")


# ============= User Info Endpoint =============
@router.get("/me", response_model=APIResponse[UserResponse])
async def get_me(current_user=Depends(get_current_user)):
    """Get current user info from JWT token."""
    return success_response(current_user, message="User info retrieved successfully")


# ============= Session Management Endpoints =============
@router.get("/sessions", response_model=APIResponse[SessionsListResponse])
async def get_sessions(
    current_user=Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    """Get all active sessions for the current user."""
    result = await service.get_sessions(current_user.id)
    return success_response(result, message="Sessions retrieved successfully")


@router.delete("/sessions/all", response_model=APIResponse[dict])
async def delete_all_sessions(
    request: Request,
    service: AuthService = Depends(get_auth_service),
):
    """Delete all sessions for the current user (logout from all devices)."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise UnauthorizedError("Missing authorization token")

    token = auth_header.replace("Bearer ", "")
    payload = verify_token(token, token_type="access")

    if not payload:
        raise UnauthorizedError("Invalid token")

    user_id = payload.get("user_id")
    if not user_id:
        raise UnauthorizedError("Invalid token payload")

    user = await service._get_user_by_id(user_id)
    if not user or not user.is_active:
        raise UnauthorizedError("User not found or inactive")

    result = await service.delete_all_sessions(user_id)
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
