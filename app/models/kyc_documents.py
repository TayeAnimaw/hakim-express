# app/models/kyc_documents.py
from sqlalchemy import Column, BigInteger, String, Date, ForeignKey, Enum, Text, TIMESTAMP
from sqlalchemy.orm import relationship
from app.database.database import Base
from datetime import datetime
import enum

class GenderEnum(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"

class IDTypeEnum(str, enum.Enum):
    passport = "passport"
    national_id = "national_id"
    driver_license = "driver_license"

class KYCStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class KYCDocument(Base):
    __tablename__ = "kyc_documents"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
        # Personal Info
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    dob = Column(Date, nullable=False)
    street_name = Column(String(100))
    house_no = Column(String(50))
    additional_info = Column(String(255))
    postal_code = Column(String(20))
    region = Column(String(50))
    city = Column(String(50))
    country = Column(String(50))
    gender = Column(Enum(GenderEnum))
    # ID Verification Fields
    id_type = Column(Enum(IDTypeEnum), default=IDTypeEnum.national_id)
    front_image = Column(String(255), nullable=False)
    back_image = Column(String(255), nullable=True)
    selfie_image = Column(String(255), nullable=False)
    # Status Tracking
    status = Column(Enum(KYCStatus), default=KYCStatus.pending)
    rejection_reason = Column(Text, nullable=True)
    verified_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="kyc_document")
