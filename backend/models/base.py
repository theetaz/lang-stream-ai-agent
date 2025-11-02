"""
Base classes and common imports for database models.
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship

# Declarative base for all models
Base = declarative_base()


def utc_now():
    """Get current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


class TimestampMixin:
    """
    Mixin to add created_at and updated_at timestamps to models.
    """

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
