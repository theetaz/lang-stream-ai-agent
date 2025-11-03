from datetime import datetime, timezone

from sqlalchemy import Column, DateTime
from sqlalchemy.orm import declarative_base

# Declarative base for all models
Base = declarative_base()


def utc_now():
    """Get current UTC datetime (timezone-naive for database compatibility)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TimestampMixin:
    """
    Mixin to add created_at and updated_at timestamps to models.
    """

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
