import hashlib
import uuid
from typing import List, Optional

from auth.jwt import create_access_token, create_refresh_token, verify_token
from auth.utils import get_device_info, hash_password, verify_password
from common.errors import UnauthorizedError, ValidationError
from fastapi import Request
from models.session import Session
from models.user import User
from schemas.auth import (
    EmailPasswordLoginRequest,
    EmailPasswordRegisterRequest,
    GoogleAuthRequest,
    RefreshRequest,
    SessionResponse,
    SessionsListResponse,
    TokenResponse,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _hash_refresh_token(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    async def _get_user_by_id(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    async def _get_user_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def _get_user_by_google_id(self, google_id: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.google_id == google_id))
        return result.scalars().first()

    async def _create_user(
        self,
        email: str,
        password_hash: Optional[str] = None,
        google_id: Optional[str] = None,
        name: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> User:
        user = User(
            email=email,
            password_hash=password_hash,
            google_id=google_id,
            name=name,
            avatar_url=avatar_url,
            is_active=True,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def _get_or_create_user_by_google(
        self,
        google_id: str,
        email: str,
        name: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> tuple[User, bool]:
        user = await self._get_user_by_google_id(google_id)
        if user:
            return user, False

        user = await self._get_user_by_email(email)
        if user:
            user.google_id = google_id
            if name and not user.name:
                user.name = name
            if avatar_url and not user.avatar_url:
                user.avatar_url = avatar_url
            await self.db.commit()
            await self.db.refresh(user)
            return user, False

        user = await self._create_user(
            email=email, google_id=google_id, name=name, avatar_url=avatar_url
        )
        return user, True

    async def _get_session_by_id(self, session_id: str) -> Optional[Session]:
        result = await self.db.execute(select(Session).where(Session.id == session_id))
        return result.scalars().first()

    async def _get_session_by_refresh_token(
        self, refresh_token: str
    ) -> Optional[Session]:
        refresh_token_hash = self._hash_refresh_token(refresh_token)
        result = await self.db.execute(
            select(Session).where(Session.refresh_token_hash == refresh_token_hash)
        )
        return result.scalars().first()

    async def _create_session(
        self,
        session_id: str,
        user_id: int,
        refresh_token: str,
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Session:
        session = Session(
            id=session_id,
            user_id=user_id,
            refresh_token_hash=self._hash_refresh_token(refresh_token),
            device_info=device_info,
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=True,
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def _update_session_activity(self, session_id: str) -> Optional[Session]:
        session = await self._get_session_by_id(session_id)
        if not session:
            return None
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def _deactivate_session(self, session_id: str) -> Optional[Session]:
        session = await self._get_session_by_id(session_id)
        if not session:
            return None
        session.is_active = False
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def _get_user_sessions(
        self, user_id: int, is_active: bool | None = None, limit: int = 50, offset: int = 0
    ) -> tuple[List[Session], int]:
        """
        Get user sessions with pagination. Returns (sessions, total_count)
        
        Args:
            user_id: The user ID
            is_active: Filter by active status (None = all sessions, True = active only, False = inactive only)
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip
        """
        from sqlalchemy import func

        # Query for total count (more efficient)
        count_query = select(func.count(Session.id)).where(Session.user_id == user_id)
        if is_active is not None:
            count_query = count_query.where(Session.is_active == is_active)
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        # Query for paginated sessions
        query = select(Session).where(Session.user_id == user_id)
        if is_active is not None:
            query = query.where(Session.is_active == is_active)
        query = query.order_by(Session.updated_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def _deactivate_all_user_sessions(self, user_id: int) -> int:
        sessions, _ = await self._get_user_sessions(user_id, is_active=True)
        for session in sessions:
            session.is_active = False
        await self.db.commit()
        return len(sessions)

    async def create_token_response(
        self, user: User, request: Request, existing_session_id: str | None = None
    ) -> dict:
        user_agent = request.headers.get("user-agent")
        ip_address = request.client.host if request.client else None
        device_info = get_device_info(user_agent)

        session_id = existing_session_id or str(uuid.uuid4())

        token_data = {
            "user_id": str(user.id),
            "email": user.email,
            "name": user.name,
            "session_id": session_id,
        }

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(
            {
                "user_id": str(user.id),
                "session_id": session_id,
            }
        )

        if existing_session_id:
            await self._update_session_activity(existing_session_id)
        else:
            await self._create_session(
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

    async def google_auth(
        self, auth_data: GoogleAuthRequest, request: Request
    ) -> TokenResponse:
        user, created = await self._get_or_create_user_by_google(
            google_id=auth_data.google_id,
            email=auth_data.email,
            name=auth_data.name,
            avatar_url=auth_data.avatar_url,
        )
        result = await self.create_token_response(user, request)
        return TokenResponse(**result)

    async def register(
        self, data: EmailPasswordRegisterRequest, request: Request
    ) -> TokenResponse:
        existing_user = await self._get_user_by_email(data.email)
        if existing_user:
            raise ValidationError("Email already registered")

        hashed_password = hash_password(data.password)
        user = await self._create_user(
            email=data.email, password_hash=hashed_password, name=data.name
        )
        result = await self.create_token_response(user, request)
        return TokenResponse(**result)

    async def login(
        self, data: EmailPasswordLoginRequest, request: Request
    ) -> TokenResponse:
        user = await self._get_user_by_email(data.email)
        if not user:
            raise UnauthorizedError("Invalid email or password")

        if not user.password_hash or not verify_password(
            data.password, user.password_hash
        ):
            raise UnauthorizedError("Invalid email or password")

        if not user.is_active:
            raise UnauthorizedError("Account is inactive")

        result = await self.create_token_response(user, request)
        return TokenResponse(**result)

    async def refresh_tokens(
        self, data: RefreshRequest, request: Request
    ) -> TokenResponse:
        payload = verify_token(data.refresh_token, token_type="refresh")
        if not payload:
            raise UnauthorizedError("Invalid refresh token")

        user_id = payload.get("user_id")
        session_id = payload.get("session_id")

        if not user_id:
            raise UnauthorizedError("Invalid token payload")

        if session_id:
            session = await self._get_session_by_refresh_token(data.refresh_token)
            if not session or not session.is_active:
                raise UnauthorizedError("Session expired or invalid")

        user = await self._get_user_by_id(user_id)
        if not user or not user.is_active:
            raise UnauthorizedError("User not found or inactive")

        result = await self.create_token_response(
            user, request, existing_session_id=session_id
        )
        return TokenResponse(**result)

    async def logout(self, request: Request, user_id: str) -> dict:
        """Logout the current user by deactivating their session."""
        # Try to get session_id from JWT token in the request
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            payload = verify_token(token, token_type="access")
            if payload:
                session_id = payload.get("session_id")
                if session_id:
                    await self._deactivate_session(session_id)
        return {"message": "Logged out successfully"}

    async def get_sessions(
        self,
        user_id: int,
        is_active: bool | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> SessionsListResponse:
        """
        Get user sessions with optional filtering and pagination.

        Args:
            user_id: The user ID
            is_active: Filter by active status (None = all sessions)
            page: Page number (starts from 1)
            per_page: Number of sessions per page
        """
        import math

        # Convert page number to offset (page 1 = offset 0)
        offset = (page - 1) * per_page

        # Get sessions with optional filtering
        sessions, total = await self._get_user_sessions(
            user_id, is_active=is_active, limit=per_page, offset=offset
        )

        # Calculate total pages
        total_pages = math.ceil(total / per_page) if total > 0 else 0

        return SessionsListResponse(
            sessions=[SessionResponse(**session.to_dict()) for session in sessions],
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
        )

    async def delete_all_sessions(self, user_id: int) -> dict:
        count = await self._deactivate_all_user_sessions(user_id)
        return {"message": f"Logged out from {count} session(s)"}

    async def delete_session(self, session_id: str, user_id: int) -> dict:
        from common.errors import ForbiddenError, NotFoundError

        session = await self._get_session_by_id(session_id)
        if not session:
            raise NotFoundError("Session not found")
        if session.user_id != user_id:
            raise ForbiddenError("Cannot delete other user's session")
        
        # Hard delete: remove the session record from the database
        await self.db.delete(session)
        await self.db.commit()
        return {"message": "Session deleted successfully"}
