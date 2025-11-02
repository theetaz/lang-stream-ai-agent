"""
Session model for tracking user sessions across devices.
Enables session management: view all sessions, logout individual sessions, logout all sessions.
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from models.base import Base, TimestampMixin


class Session(Base, TimestampMixin):
    """
    Session model for tracking active user sessions.
    
    Attributes:
        id: Primary key (session ID, stored in JWT token)
        user_id: Foreign key to users table
        refresh_token_hash: Hash of the refresh token for this session
        device_info: Device/browser information
        ip_address: IP address where session was created
        user_agent: User agent string
        is_active: Whether the session is active
        last_activity: Timestamp of last activity (updated_at)
        created_at: When the session was created
        updated_at: When the session was last updated
    """
    
    __tablename__ = "sessions"
    
    id = Column(String(255), primary_key=True, index=True)  # UUID session ID
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    refresh_token_hash = Column(String(255), nullable=False, unique=True, index=True)
    device_info = Column(String(255), nullable=True)  # Device name/browser
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    user_agent = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationship
    user = relationship("User", backref="sessions")
    
    def __repr__(self) -> str:
        return f"<Session(id={self.id}, user_id={self.user_id}, is_active={self.is_active})>"
    
    def to_dict(self) -> dict:
        """
        Convert session model to dictionary for API responses.
        
        Returns:
            Dictionary with session data
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "device_info": self.device_info,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_activity": self.updated_at.isoformat() if self.updated_at else None,
        }

