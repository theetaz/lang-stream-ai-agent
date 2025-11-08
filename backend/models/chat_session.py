from models.base import Base, TimestampMixin, UUIDMixin
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class ChatSession(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "chat_sessions"
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(255), nullable=True)
    last_message_at = Column(DateTime, nullable=True)
    is_archived = Column(Boolean, default=False, nullable=False)
    is_pinned = Column(Boolean, default=False, nullable=False, index=True)

    user = relationship("User", back_populates="chat_sessions")
    messages = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan"
    )
    files = relationship("UploadedFile", back_populates="session")
