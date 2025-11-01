"""
Base classes and common imports for database models.
"""
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

# Declarative base for all models
Base = declarative_base()


class TimestampMixin:
    """
    Mixin to add created_at and updated_at timestamps to models.
    """
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


# Export commonly used SQLAlchemy types
__all__ = [
    "Base",
    "TimestampMixin",
    "Column",
    "Integer",
    "String",
    "DateTime",
    "Text",
    "Boolean",
    "ForeignKey",
    "relationship",
    "datetime",
]
