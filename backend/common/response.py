from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""

    success: bool
    message: str
    data: Optional[T] = None
    metadata: Optional[dict] = None


def success_response(
    data: T, message: str = "Success", metadata: Optional[dict] = None
) -> APIResponse[T]:
    """Create a success response."""
    return APIResponse(success=True, message=message, data=data, metadata=metadata)


def error_response(
    message: str, data: Optional[T] = None, metadata: Optional[dict] = None
) -> APIResponse[T]:
    """Create an error response."""
    return APIResponse(success=False, message=message, data=data, metadata=metadata)
