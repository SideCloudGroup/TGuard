"""Database models for TGuard bot."""

from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, BigInteger, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class RequestStatus(str, Enum):
    """Request status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class JoinRequest(Base):
    """Join request model."""
    __tablename__ = "join_requests"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    chat_id = Column(BigInteger, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=True)
    verification_token = Column(String(64), nullable=False, unique=True, index=True)
    status = Column(String(20), nullable=False, default=RequestStatus.PENDING, index=True)
    request_time = Column(DateTime, nullable=False, default=func.now())
    processed_time = Column(DateTime, nullable=True)
    admin_id = Column(BigInteger, nullable=True)
    verification_completed = Column(Boolean, nullable=False, default=False)
    
    def __repr__(self):
        return f"<JoinRequest(user_id={self.user_id}, chat_id={self.chat_id}, status={self.status})>"


class VerificationSession(Base):
    """Verification session model."""
    __tablename__ = "verification_sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String(64), nullable=False, unique=True, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    chat_id = Column(BigInteger, nullable=False, index=True)
    captcha_completed = Column(Boolean, nullable=False, default=False)
    captcha_response = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    created_time = Column(DateTime, nullable=False, default=func.now())
    completed_time = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.utcnow() > self.expires_at
    
    def __repr__(self):
        return f"<VerificationSession(token={self.token}, user_id={self.user_id}, completed={self.captcha_completed})>"


class BotSettings(Base):
    """Bot settings model."""
    __tablename__ = "bot_settings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, nullable=False, unique=True, index=True)
    verification_timeout = Column(Integer, nullable=False, default=300)  # 5 minutes
    welcome_message = Column(Text, nullable=True)
    rejection_message = Column(Text, nullable=True)
    auto_approve = Column(Boolean, nullable=False, default=True)
    max_verification_attempts = Column(Integer, nullable=False, default=3)
    created_time = Column(DateTime, nullable=False, default=func.now())
    updated_time = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<BotSettings(chat_id={self.chat_id}, auto_approve={self.auto_approve})>"
