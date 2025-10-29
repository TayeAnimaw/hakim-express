# app/models/recipient.py
from sqlalchemy import Column, BigInteger, String, ForeignKey, Boolean, Enum, TIMESTAMP
from sqlalchemy.orm import relationship
from app.database.database import Base
from datetime import datetime
import enum

class AccountType(enum.Enum):
    bank_account = "bank_account"
    telebirr = "telebirr"

class Recipient(Base):
    __tablename__ = 'recipients'

    recipient_id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id', ondelete="CASCADE"), nullable=False)
    full_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    account_type = Column(Enum(AccountType), nullable=False)
    bank_name = Column(String(100), nullable=True)
    account_number = Column(String(50), nullable=True)
    telebirr_number = Column(String(50), nullable=True)
    amount = Column(String(50), default=0.0)
    is_verified = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    # user = relationship('User', back_populates='recipients')
    # transactions = relationship('Transaction', back_populates='recipient')
