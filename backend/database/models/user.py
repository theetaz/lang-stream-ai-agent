"""
User model for authentication and user management.
Designed for Google OAuth integration with Better Auth.
"""
from sqlalchemy import Column, Integer, String, Boolean
from database.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """
    User model for storing user information from Google OAuth.

    Attributes:
        id: Primary key
        email: User's email address (unique, required)
        google_id: Google OAuth user ID (unique, optional for future auth methods)
        name: User's full name
        avatar_url: URL to user's profile picture
        is_active: Whether the user account is active
        created_at: When the user was created (from TimestampMixin)
        updated_at: When the user was last updated (from TimestampMixin)
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    name = Column(String(255), nullable=True)
    avatar_url = Column(String(512), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}')>"

    def to_dict(self) -> dict:
        """
        Convert user model to dictionary for API responses.

        Returns:
            Dictionary with user data (excluding sensitive info)
        """
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "avatar_url": self.avatar_url,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
