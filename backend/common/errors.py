"""
Custom exception classes for API errors.
All business logic errors should inherit from AppError.
"""
from fastapi import HTTPException


class AppError(HTTPException):
    """Base exception for application errors."""
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


class ValidationError(AppError):
    """Validation error (400)."""
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)


class NotFoundError(AppError):
    """Resource not found error (404)."""
    def __init__(self, detail: str):
        super().__init__(status_code=404, detail=detail)


class UnauthorizedError(AppError):
    """Unauthorized error (401)."""
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(status_code=401, detail=detail)


class ForbiddenError(AppError):
    """Forbidden error (403)."""
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(status_code=403, detail=detail)


def app_error_handler(request, exc: AppError):
    """Global exception handler for AppError."""
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.detail, "data": None}
    )

