"""
User management API routes.
Only HTTP handling and service calls. No business logic.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database.db_client import get_db
from api.v1.user.service import UserService
from schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
)


router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Dependency to get UserService instance."""
    return UserService(db)


@router.post("", response_model=UserResponse, status_code=201)
async def create_user_endpoint(
    user: UserCreate,
    service: UserService = Depends(get_user_service),
):
    """Create a new user."""
    return await service.create_user(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_endpoint(
    user_id: int,
    service: UserService = Depends(get_user_service),
):
    """Get a user by ID."""
    return await service.get_user(user_id)


@router.get("/email/{email}", response_model=UserResponse)
async def get_user_by_email_endpoint(
    email: str,
    service: UserService = Depends(get_user_service),
):
    """Get a user by email address."""
    return await service.get_user_by_email(email)


@router.get("", response_model=UserListResponse)
async def list_users_endpoint(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of users to return"),
    active_only: bool = Query(False, description="Only return active users"),
    service: UserService = Depends(get_user_service),
):
    """List users with pagination."""
    return await service.list_users(skip=skip, limit=limit, active_only=active_only)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user_endpoint(
    user_id: int,
    user_update: UserUpdate,
    service: UserService = Depends(get_user_service),
):
    """Update user information."""
    return await service.update_user(user_id, user_update)


@router.delete("/{user_id}", status_code=204)
async def delete_user_endpoint(
    user_id: int,
    service: UserService = Depends(get_user_service),
):
    """Delete a user (hard delete)."""
    await service.delete_user(user_id)


@router.post("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user_endpoint(
    user_id: int,
    service: UserService = Depends(get_user_service),
):
    """Deactivate a user (soft delete)."""
    return await service.deactivate_user(user_id)

