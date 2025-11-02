"""
User management service layer.
Contains all business logic for user operations.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from database.crud.user_crud import (
    create_user,
    get_user_by_id,
    get_user_by_email,
    list_users,
    update_user,
    delete_user,
    deactivate_user,
)
from schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
)
from common.errors import ValidationError, NotFoundError


class UserService:
    """Service for user management operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, data: UserCreate) -> UserResponse:
        """Create a new user."""
        try:
            db_user = await create_user(
                db=self.db,
                email=data.email,
                google_id=data.google_id,
                name=data.name,
                avatar_url=data.avatar_url,
            )
            return UserResponse.model_validate(db_user)
        except IntegrityError as e:
            await self.db.rollback()
            if "email" in str(e):
                raise ValidationError(f"User with email {data.email} already exists")
            elif "google_id" in str(e):
                raise ValidationError(f"User with google_id {data.google_id} already exists")
            else:
                raise ValidationError("Database integrity error")

    async def get_user(self, user_id: int) -> UserResponse:
        """Get a user by ID."""
        user = await get_user_by_id(self.db, user_id)

        if not user:
            raise NotFoundError(f"User {user_id} not found")

        return UserResponse.model_validate(user)

    async def get_user_by_email(self, email: str) -> UserResponse:
        """Get a user by email address."""
        user = await get_user_by_email(self.db, email)

        if not user:
            raise NotFoundError(f"User with email {email} not found")

        return UserResponse.model_validate(user)

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
    ) -> UserListResponse:
        """List users with pagination."""
        users = await list_users(self.db, skip=skip, limit=limit, active_only=active_only)

        return UserListResponse(
            users=[UserResponse.model_validate(user) for user in users],
            total=len(users),  # In production, you'd want a separate count query
            skip=skip,
            limit=limit,
        )

    async def update_user(self, user_id: int, data: UserUpdate) -> UserResponse:
        """Update user information."""
        try:
            updated_user = await update_user(
                db=self.db,
                user_id=user_id,
                email=data.email,
                name=data.name,
                avatar_url=data.avatar_url,
                is_active=data.is_active,
            )

            if not updated_user:
                raise NotFoundError(f"User {user_id} not found")

            return UserResponse.model_validate(updated_user)
        except IntegrityError as e:
            await self.db.rollback()
            if "email" in str(e):
                raise ValidationError(f"User with email {data.email} already exists")
            else:
                raise ValidationError("Database integrity error")

    async def delete_user(self, user_id: int) -> None:
        """Delete a user (hard delete)."""
        deleted = await delete_user(self.db, user_id)

        if not deleted:
            raise NotFoundError(f"User {user_id} not found")

    async def deactivate_user(self, user_id: int) -> UserResponse:
        """Deactivate a user (soft delete)."""
        user = await deactivate_user(self.db, user_id)

        if not user:
            raise NotFoundError(f"User {user_id} not found")

        return UserResponse.model_validate(user)

