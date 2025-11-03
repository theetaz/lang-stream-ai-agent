from fastapi import HTTPException, status


class AppError(HTTPException):
    """Base exception for application errors."""

    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


class ValidationError(AppError):
    """Validation error (400)."""

    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class NotFoundError(AppError):
    """Resource not found error (404)."""

    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class UnauthorizedError(AppError):
    """Unauthorized error (401)."""

    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class ForbiddenError(AppError):
    """Forbidden error (403)."""

    def __init__(self, detail: str = "Forbidden"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def app_error_handler(request, exc: AppError):
    """Global exception handler for AppError."""
    from fastapi.responses import JSONResponse
    from common.response import error_response

    response = error_response(message=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(),
    )
