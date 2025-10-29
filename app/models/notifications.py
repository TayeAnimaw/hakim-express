# app/models/notifications.py
from sqlalchemy import Column, BigInteger, String, Text, Enum, Boolean, TIMESTAMP, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database.database import Base
from datetime import datetime
import enum

class ChannelType(str, enum.Enum):
    email = "email"
    sms = "sms"
    push = "push"

class Notification(Base):
    __tablename__ = 'notifications'

    notification_id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id', ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    channel = Column(Enum(ChannelType), nullable=False)
    type = Column(String(50), nullable=False)
    is_sent = Column(Boolean, default=False)
    sent_at = Column(TIMESTAMP, nullable=True)
    is_read = Column(Boolean, default=False)
    doc_metadata = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship('User', back_populates='notifications')

    __table_args__ = (
        Index('ix_user_is_read', 'user_id', 'is_read'),
    )