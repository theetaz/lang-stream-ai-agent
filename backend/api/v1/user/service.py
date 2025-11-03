from typing import Optional

from common.errors import NotFoundError, ValidationError
from models.user import User
from schemas.user import UserCreate, UserListResponse, UserResponse, UserUpdate
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_user_by_id(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    async def _get_user_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def _get_user_by_google_id(self, google_id: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.google_id == google_id))
        return result.scalars().first()

    async def create_user(self, data: UserCreate) -> UserResponse:
        try:
            user = User(
                email=data.email,
                google_id=data.google_id,
                name=data.name,
                avatar_url=data.avatar_url,
                is_active=True,
            )
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            return UserResponse.model_validate(user)
        except IntegrityError as e:
            await self.db.rollback()
            if "email" in str(e):
                raise ValidationError(f"User with email {data.email} already exists")
            elif "google_id" in str(e):
                raise ValidationError(
                    f"User with google_id {data.google_id} already exists"
                )
            raise ValidationError("Database integrity error")

    async def get_user(self, user_id: int) -> UserResponse:
        user = await self._get_user_by_id(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        return UserResponse.model_validate(user)

    async def get_user_by_email_str(self, email: str) -> UserResponse:
        user = await self._get_user_by_email(email)
        if not user:
            raise NotFoundError(f"User with email {email} not found")
        return UserResponse.model_validate(user)

    async def list_users(
        self, skip: int = 0, limit: int = 100, active_only: bool = False
    ) -> UserListResponse:
        query = select(User)
        if active_only:
            query = query.where(User.is_active == True)
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        users = list(result.scalars().all())
        return UserListResponse(
            users=[UserResponse.model_validate(user) for user in users],
            total=len(users),
            skip=skip,
            limit=limit,
        )

    async def update_user(self, user_id: int, data: UserUpdate) -> UserResponse:
        try:
            user = await self._get_user_by_id(user_id)
            if not user:
                raise NotFoundError(f"User {user_id} not found")

            if data.email is not None:
                user.email = data.email
            if data.name is not None:
                user.name = data.name
            if data.avatar_url is not None:
                user.avatar_url = data.avatar_url
            if data.is_active is not None:
                user.is_active = data.is_active

            await self.db.commit()
            await self.db.refresh(user)
            return UserResponse.model_validate(user)
        except IntegrityError as e:
            await self.db.rollback()
            if "email" in str(e):
                raise ValidationError(f"User with email {data.email} already exists")
            raise ValidationError("Database integrity error")

    async def delete_user(self, user_id: int) -> None:
        user = await self._get_user_by_id(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        await self.db.delete(user)
        await self.db.commit()

    async def deactivate_user(self, user_id: int) -> UserResponse:
        user = await self._get_user_by_id(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        user.is_active = False
        await self.db.commit()
        await self.db.refresh(user)
        return UserResponse.model_validate(user)
