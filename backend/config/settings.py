"""
Application configuration settings.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def get_settings():
    """Get application settings."""
    return {
        "postgres_user": os.getenv("POSTGRES_USER", "postgres"),
        "postgres_password": os.getenv("POSTGRES_PASSWORD", ""),
        "postgres_host": os.getenv("POSTGRES_HOST", "localhost"),
        "postgres_port": os.getenv("POSTGRES_PORT", "5432"),
        "postgres_db": os.getenv("POSTGRES_DB", "lang_ai_agent"),
        "jwt_secret": os.getenv("JWT_SECRET", os.getenv("BETTER_AUTH_SECRET", "your-secret-key-change-in-production")),
        "access_token_expire_minutes": int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
        "refresh_token_expire_days": int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")),
        "cors_origins": os.getenv("CORS_ORIGINS", "http://localhost:3000,http://frontend:3000").split(","),
    }

