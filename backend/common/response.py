"""
Standard API response utilities.
Provides consistent response format across all endpoints.
"""
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar('T')


class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    success: bool
    message: str
    data: Optional[T] = None


def success_response(
    data: T,
    message: str = "Success"
) -> APIResponse[T]:
    """Create a success response."""
    return APIResponse(success=True, message=message, data=data)


def error_response(
    message: str,
    data: Optional[T] = None
) -> APIResponse[T]:
    """Create an error response."""
    return APIResponse(success=False, message=message, data=data)

