"""
Async CRUD operations for User model.
All operations are non-blocking and use async/await.
"""
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.user import User


async def create_user(
    db: AsyncSession,
    email: str,
    google_id: Optional[str] = None,
    name: Optional[str] = None,
    avatar_url: Optional[str] = None,
) -> User:
    """
    Create a new user in the database.

    Args:
        db: Async database session
        email: User's email address (required, unique)
        google_id: Google OAuth user ID (optional, unique)
        name: User's full name (optional)
        avatar_url: URL to user's profile picture (optional)

    Returns:
        The created User object

    Raises:
        IntegrityError: If email or google_id already exists
    """
    user = User(
        email=email,
        google_id=google_id,
        name=name,
        avatar_url=avatar_url,
        is_active=True,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """
    Get a user by their ID.

    Args:
        db: Async database session
        user_id: User's ID

    Returns:
        User object if found, None otherwise
    """
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    Get a user by their email address.

    Args:
        db: Async database session
        email: User's email address

    Returns:
        User object if found, None otherwise
    """
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def get_user_by_google_id(db: AsyncSession, google_id: str) -> Optional[User]:
    """
    Get a user by their Google OAuth ID.

    Args:
        db: Async database session
        google_id: User's Google OAuth ID

    Returns:
        User object if found, None otherwise
    """
    result = await db.execute(select(User).where(User.google_id == google_id))
    return result.scalars().first()


async def get_or_create_user_by_google(
    db: AsyncSession,
    google_id: str,
    email: str,
    name: Optional[str] = None,
    avatar_url: Optional[str] = None,
) -> tuple[User, bool]:
    """
    Get or create a user by their Google OAuth ID.
    This is useful for OAuth login flow.

    Args:
        db: Async database session
        google_id: User's Google OAuth ID
        email: User's email address
        name: User's full name (optional)
        avatar_url: URL to user's profile picture (optional)

    Returns:
        Tuple of (User object, created: bool)
        created is True if the user was created, False if found
    """
    # Try to find existing user by Google ID
    user = await get_user_by_google_id(db, google_id)

    if user:
        return user, False

    # Try to find by email (user might have registered before)
    user = await get_user_by_email(db, email)

    if user:
        # Update Google ID if found by email
        user.google_id = google_id
        if name and not user.name:
            user.name = name
        if avatar_url and not user.avatar_url:
            user.avatar_url = avatar_url

        await db.commit()
        await db.refresh(user)
        return user, False

    # Create new user
    user = await create_user(
        db=db,
        email=email,
        google_id=google_id,
        name=name,
        avatar_url=avatar_url,
    )

    return user, True


async def update_user(
    db: AsyncSession,
    user_id: int,
    email: Optional[str] = None,
    name: Optional[str] = None,
    avatar_url: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> Optional[User]:
    """
    Update user information.

    Args:
        db: Async database session
        user_id: User's ID
        email: New email (optional)
        name: New name (optional)
        avatar_url: New avatar URL (optional)
        is_active: New active status (optional)

    Returns:
        Updated User object if found, None otherwise
    """
    user = await get_user_by_id(db, user_id)

    if not user:
        return None

    if email is not None:
        user.email = email
    if name is not None:
        user.name = name
    if avatar_url is not None:
        user.avatar_url = avatar_url
    if is_active is not None:
        user.is_active = is_active

    await db.commit()
    await db.refresh(user)

    return user


async def list_users(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
) -> List[User]:
    """
    List users with pagination.

    Args:
        db: Async database session
        skip: Number of users to skip (for pagination)
        limit: Maximum number of users to return
        active_only: If True, only return active users

    Returns:
        List of User objects
    """
    query = select(User)

    if active_only:
        query = query.where(User.is_active == True)

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    return list(result.scalars().all())


async def delete_user(db: AsyncSession, user_id: int) -> bool:
    """
    Delete a user by ID.

    Args:
        db: Async database session
        user_id: User's ID

    Returns:
        True if user was deleted, False if not found
    """
    user = await get_user_by_id(db, user_id)

    if not user:
        return False

    await db.delete(user)
    await db.commit()

    return True


async def deactivate_user(db: AsyncSession, user_id: int) -> Optional[User]:
    """
    Deactivate a user (soft delete).

    Args:
        db: Async database session
        user_id: User's ID

    Returns:
        Updated User object if found, None otherwise
    """
    return await update_user(db, user_id, is_active=False)
