"""
User management API endpoints.
All endpoints use async operations for non-blocking database access.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from database import get_async_db
from database.crud import (
    create_user,
    get_user_by_id,
    get_user_by_email,
    list_users,
    update_user,
    delete_user,
    deactivate_user,
)
from api.schemas.user_schema import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserResponse, status_code=201)
async def create_user_endpoint(
    user: UserCreate,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Create a new user.

    Args:
        user: User data
        db: Database session (injected)

    Returns:
        Created user data

    Raises:
        400: If email or google_id already exists
    """
    try:
        db_user = await create_user(
            db=db,
            email=user.email,
            google_id=user.google_id,
            name=user.name,
            avatar_url=user.avatar_url,
        )
        return db_user
    except IntegrityError as e:
        await db.rollback()
        if "email" in str(e):
            raise HTTPException(
                status_code=400,
                detail=f"User with email {user.email} already exists",
            )
        elif "google_id" in str(e):
            raise HTTPException(
                status_code=400,
                detail=f"User with google_id {user.google_id} already exists",
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Database integrity error",
            )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_endpoint(
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get a user by ID.

    Args:
        user_id: User ID
        db: Database session (injected)

    Returns:
        User data

    Raises:
        404: If user not found
    """
    user = await get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")

    return user


@router.get("/email/{email}", response_model=UserResponse)
async def get_user_by_email_endpoint(
    email: str,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get a user by email address.

    Args:
        email: User's email address
        db: Database session (injected)

    Returns:
        User data

    Raises:
        404: If user not found
    """
    user = await get_user_by_email(db, email)

    if not user:
        raise HTTPException(status_code=404, detail=f"User with email {email} not found")

    return user


@router.get("", response_model=UserListResponse)
async def list_users_endpoint(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of users to return"),
    active_only: bool = Query(False, description="Only return active users"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    List users with pagination.

    Args:
        skip: Number of users to skip (for pagination)
        limit: Maximum number of users to return
        active_only: If True, only return active users
        db: Database session (injected)

    Returns:
        List of users with pagination info
    """
    users = await list_users(db, skip=skip, limit=limit, active_only=active_only)

    return UserListResponse(
        users=users,
        total=len(users),  # In production, you'd want a separate count query
        skip=skip,
        limit=limit,
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user_endpoint(
    user_id: int,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Update user information.

    Args:
        user_id: User ID
        user_update: Fields to update
        db: Database session (injected)

    Returns:
        Updated user data

    Raises:
        404: If user not found
        400: If email already exists
    """
    try:
        updated_user = await update_user(
            db=db,
            user_id=user_id,
            email=user_update.email,
            name=user_update.name,
            avatar_url=user_update.avatar_url,
            is_active=user_update.is_active,
        )

        if not updated_user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")

        return updated_user
    except IntegrityError as e:
        await db.rollback()
        if "email" in str(e):
            raise HTTPException(
                status_code=400,
                detail=f"User with email {user_update.email} already exists",
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Database integrity error",
            )


@router.delete("/{user_id}", status_code=204)
async def delete_user_endpoint(
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Delete a user (hard delete).

    Args:
        user_id: User ID
        db: Database session (injected)

    Returns:
        No content

    Raises:
        404: If user not found
    """
    deleted = await delete_user(db, user_id)

    if not deleted:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")


@router.post("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user_endpoint(
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Deactivate a user (soft delete).

    Args:
        user_id: User ID
        db: Database session (injected)

    Returns:
        Deactivated user data

    Raises:
        404: If user not found
    """
    user = await deactivate_user(db, user_id)

    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")

    return user
