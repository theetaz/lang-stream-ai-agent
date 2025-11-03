from pydantic import BaseModel, EmailStr


class GoogleAuthRequest(BaseModel):
    """Request from frontend after Google OAuth success"""

    google_id: str
    email: EmailStr
    name: str | None = None
    avatar_url: str | None = None


class EmailPasswordRegisterRequest(BaseModel):
    """Request for email/password registration"""

    email: EmailStr
    password: str
    name: str | None = None


class EmailPasswordLoginRequest(BaseModel):
    """Request for email/password login"""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict
    session_id: str


class RefreshRequest(BaseModel):
    """Request to refresh access token"""

    refresh_token: str


class UserResponse(BaseModel):
    """User info response"""

    id: int
    email: str
    name: str | None
    avatar_url: str | None
    is_active: bool


class SessionResponse(BaseModel):
    """Session info response"""

    id: str
    device_info: str | None
    ip_address: str | None
    user_agent: str | None
    is_active: bool
    created_at: str
    updated_at: str
    last_activity: str


class SessionsListResponse(BaseModel):
    """List of sessions response"""

    sessions: list[SessionResponse]
