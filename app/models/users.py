# app/models/users.py
from sqlalchemy import Column, BigInteger, String, Boolean, TIMESTAMP, Text, Enum
from sqlalchemy.orm import relationship
from app.database.database import Base
import enum
from datetime import datetime

class Role(str, enum.Enum):
    user = "user"
    admin = "admin"
    finance_officer = "finance_officer"
    support = "support"

class KYCStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class User(Base):
    __tablename__ = 'users'

    user_id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    email = Column(String, unique=False, index=True, nullable=True)
    phone = Column(String, unique=False, index=True, nullable=True)
    password = Column(String(255), nullable=False)
    role = Column(Enum(Role), default=Role.user, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_flagged = Column(Boolean, default=False)
    suspended_at = Column(TIMESTAMP, nullable=True)
    suspension_reason = Column(Text, nullable=True)
    last_login = Column(TIMESTAMP, nullable=True)
    two_factor_enabled = Column(Boolean, default=False)
    kyc_status = Column(Enum(KYCStatus), default=KYCStatus.pending)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(TIMESTAMP, nullable=True)
    otp_code = Column(String(6), nullable=True)
    otp_expires_at = Column(TIMESTAMP, nullable=True)
    user_weekly_limit = Column(BigInteger, nullable=True)
    admin_notes = Column(Text, nullable=True)
    stripe_customer_id = Column(String, nullable=True)
    # Profile picture (nullable, backward compatible)
    profile_picture = Column(String(255), nullable=True)
    # Relationships
    kyc_document = relationship("KYCDocument", uselist=False, back_populates="user", cascade="all, delete-orphan")
    # recipients = relationship("Recipient", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    payment_cards = relationship("PaymentCard", back_populates="user", cascade="all, delete-orphan")
    # user_limits = relationship("UserLimit", back_populates="user")
    # manual_deposits = relationship("ManualDeposit", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    admin_role = relationship("AdminRole", uselist=False, back_populates="user", cascade="all, delete-orphan")

    # Add other relationships as needed

