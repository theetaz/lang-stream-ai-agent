from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema with common fields."""

    email: EmailStr = Field(..., description="User's email address")
    name: Optional[str] = Field(None, max_length=255, description="User's full name")
    avatar_url: Optional[str] = Field(
        None, max_length=512, description="URL to user's profile picture"
    )


class UserCreate(UserBase):
    """Schema for creating a new user."""

    google_id: Optional[str] = Field(
        None, max_length=255, description="Google OAuth user ID"
    )


class UserUpdate(BaseModel):
    """Schema for updating user information."""

    email: Optional[EmailStr] = Field(None, description="New email address")
    name: Optional[str] = Field(None, max_length=255, description="New name")
    avatar_url: Optional[str] = Field(
        None, max_length=512, description="New avatar URL"
    )
    is_active: Optional[bool] = Field(None, description="Active status")


class UserResponse(UserBase):
    """Schema for user response."""

    id: int = Field(..., description="User ID")
    google_id: Optional[str] = Field(None, description="Google OAuth user ID")
    is_active: bool = Field(..., description="Whether the user account is active")
    created_at: datetime = Field(..., description="When the user was created")
    updated_at: datetime = Field(..., description="When the user was last updated")

    class Config:
        from_attributes = True  # Allow ORM model to dict conversion


class UserListResponse(BaseModel):
    """Schema for paginated user list response."""

    users: list[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    skip: int = Field(..., description="Number of users skipped")
    limit: int = Field(..., description="Maximum number of users returned")
