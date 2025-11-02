"""
Common utility functions.
"""
from passlib.context import CryptContext
from user_agents import parse as parse_user_agent


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_device_info(user_agent: str | None) -> str | None:
    """Extract device info from user agent string."""
    if not user_agent:
        return None
    
    try:
        ua = parse_user_agent(user_agent)
        device = ua.device.family if ua.device.family != "Other" else None
        os = f"{ua.os.family} {ua.os.version_string}".strip() if ua.os.family != "Other" else None
        browser = f"{ua.browser.family} {ua.browser.version_string}".strip() if ua.browser.family != "Other" else None
        
        parts = [p for p in [device, os, browser] if p]
        return ", ".join(parts) if parts else None
    except Exception:
        return None

