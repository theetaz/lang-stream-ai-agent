"""
Authentication service layer.
Contains all business logic for authentication operations.
"""
import uuid
from fastapi import Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from auth.jwt import create_access_token, create_refresh_token, verify_token
from database.crud.user_crud import (
    get_or_create_user_by_google,
    get_user_by_email,
    create_user,
    get_user_by_id,
)
from database.crud.session_crud import (
    create_session,
    get_session_by_refresh_token,
    get_user_sessions,
    deactivate_session,
    deactivate_all_user_sessions,
    update_session_activity,
)
from common.utils import hash_password, verify_password, get_device_info
from schemas.auth import (
    GoogleAuthRequest,
    EmailPasswordRegisterRequest,
    EmailPasswordLoginRequest,
    TokenResponse,
    RefreshRequest,
    SessionResponse,
    SessionsListResponse,
)


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_token_response(
        self,
        user,
        request: Request,
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
            await update_session_activity(self.db, existing_session_id)
        else:
            # Create new session
            await create_session(
                db=self.db,
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

    async def google_auth(self, auth_data: GoogleAuthRequest, request: Request) -> TokenResponse:
        """Handle Google OAuth login/registration."""
        try:
            # Get or create user
            user, created = await get_or_create_user_by_google(
                db=self.db,
                google_id=auth_data.google_id,
                email=auth_data.email,
                name=auth_data.name,
                avatar_url=auth_data.avatar_url,
            )

            # Create and return JWT tokens with session
            result = await self.create_token_response(user, request)
            return TokenResponse(**result)

        except Exception as e:
            print(f"Google auth error: {e}")
            raise HTTPException(status_code=500, detail="Authentication failed")

    async def register(self, data: EmailPasswordRegisterRequest, request: Request) -> TokenResponse:
        """Register a new user with email and password."""
        # Check if user already exists
        existing_user = await get_user_by_email(self.db, data.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Hash password
        hashed_password = hash_password(data.password)

        # Create user
        user = await create_user(
            db=self.db,
            email=data.email,
            password_hash=hashed_password,
            name=data.name,
        )

        result = await self.create_token_response(user, request)
        return TokenResponse(**result)

    async def login(self, data: EmailPasswordLoginRequest, request: Request) -> TokenResponse:
        """Login with email and password."""
        # Get user
        user = await get_user_by_email(self.db, data.email)

        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        # Verify password
        if not user.password_hash or not verify_password(data.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not user.is_active:
            raise HTTPException(status_code=401, detail="Account is inactive")

        result = await self.create_token_response(user, request)
        return TokenResponse(**result)

    async def refresh_tokens(self, data: RefreshRequest, request: Request) -> TokenResponse:
        """Refresh access token using refresh token."""
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
            session = await get_session_by_refresh_token(self.db, data.refresh_token)
            if not session or not session.is_active:
                raise HTTPException(status_code=401, detail="Session expired or invalid")

        # Get user
        user = await get_user_by_id(self.db, user_id)

        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive")

        # Create new tokens with same session_id
        result = await self.create_token_response(user, request, existing_session_id=session_id)
        return TokenResponse(**result)

    async def logout(self, request: Request) -> dict:
        """Logout endpoint - deactivates current session."""
        # Get session_id from token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            payload = verify_token(token, token_type="access")
            if payload:
                session_id = payload.get("session_id")
                if session_id:
                    await deactivate_session(self.db, session_id)
        
        return {"message": "Logged out successfully"}

    async def get_sessions(self, user_id: int) -> SessionsListResponse:
        """Get all sessions for a user."""
        sessions = await get_user_sessions(self.db, user_id, active_only=False)
        
        return SessionsListResponse(
            sessions=[SessionResponse(**session.to_dict()) for session in sessions]
        )

    async def delete_all_sessions(self, user_id: int) -> dict:
        """Delete all sessions for a user."""
        count = await deactivate_all_user_sessions(self.db, user_id)
        return {"message": f"Logged out from {count} session(s)"}

    async def delete_session(self, session_id: str, user_id: int) -> dict:
        """Delete a specific session by session_id."""
        from database.crud.session_crud import get_session_by_id
        
        session = await get_session_by_id(self.db, session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session.user_id != user_id:
            raise HTTPException(status_code=403, detail="Cannot delete other user's session")
        
        await deactivate_session(self.db, session_id)
        
        return {"message": "Session deleted successfully"}

