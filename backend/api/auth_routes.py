"""
Authentication API endpoints with JWT tokens.
Supports both Google OAuth (SSO) and email/password authentication.
Frontend handles OAuth callback, backend creates user and issues JWT tokens.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext

from auth.jwt import create_access_token, create_refresh_token, verify_token
from database import get_async_db
from database.crud import (
    get_or_create_user_by_google,
    get_user_by_email,
    create_user,
    get_user_by_id,
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


def create_token_response(user) -> dict:
    """Create JWT tokens and format response"""
    token_data = {
        "user_id": user.id,
        "email": user.email,
        "name": user.name,
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"user_id": user.id})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user.to_dict(),
    }


async def get_current_user(request: Request, db: AsyncSession = Depends(get_async_db)):
    """Dependency to get current user from JWT token"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")

    token = auth_header.replace("Bearer ", "")
    payload = verify_token(token, token_type="access")

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = await get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return user


# ============= SSO (Google OAuth) Endpoints =============

@router.post("/google", response_model=TokenResponse)
async def google_auth(
    auth_data: GoogleAuthRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Handle Google OAuth login/registration.
    Frontend sends user data after successful OAuth, backend creates user and returns JWT.

    Flow:
    1. Frontend handles Google OAuth and gets user info
    2. Frontend sends user info to this endpoint
    3. Backend creates/gets user in database
    4. Backend returns JWT tokens
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

        # Create and return JWT tokens
        return create_token_response(user)

    except Exception as e:
        print(f"Google auth error: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")


# ============= Email/Password Endpoints =============

@router.post("/register", response_model=TokenResponse)
async def register(
    data: EmailPasswordRegisterRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Register a new user with email and password.

    Args:
        data: Email, password, and optional name

    Returns:
        JWT tokens and user info
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
        name=data.name,
        # Store hashed password in a new field (need to add to User model)
    )

    # For now, we'll store password in google_id field (temporary hack)
    # TODO: Add password field to User model
    user.google_id = hashed_password
    await db.commit()
    await db.refresh(user)

    return create_token_response(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: EmailPasswordLoginRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Login with email and password.

    Args:
        data: Email and password

    Returns:
        JWT tokens and user info
    """
    # Get user
    user = await get_user_by_email(db, data.email)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Verify password (stored in google_id field temporarily)
    # TODO: Add proper password field to User model
    if not user.google_id or not verify_password(data.password, user.google_id):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account is inactive")

    return create_token_response(user)


# ============= Token Management Endpoints =============

@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Refresh access token using refresh token.

    Args:
        data: Refresh token

    Returns:
        New JWT tokens
    """
    # Verify refresh token
    payload = verify_token(data.refresh_token, token_type="refresh")

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    # Get user
    user = await get_user_by_id(db, user_id)

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # Create new tokens
    return create_token_response(user)


@router.post("/logout")
async def logout():
    """
    Logout endpoint.
    Client should remove tokens from storage.
    """
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
