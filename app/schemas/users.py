# app/schemas/users.py
from pydantic import BaseModel, EmailStr, constr, validator, Field, root_validator
from typing import Optional
from enum import Enum
from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Boolean, TIMESTAMP, Text, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from app.schemas.kyc_documents import KYCDocumentUser, KycDocumentBase
class KYCStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class Role(str, Enum):
    user = "user"
    admin = "admin"
    finance_officer = "finance_officer"
    support = "support"
class OTPVerify(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    otp: str
class ReSendOTPRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[constr(min_length=10, max_length=15)] = None # type: ignore
    role: Role = Role.user
    kyc_documents: KycDocumentBase | None = None
    profile_picture: Optional[str] = None
    

class UserCreate(BaseModel):     
    email: Optional[EmailStr] = None
    phone: Optional[constr(min_length=10, max_length=15)] = None # type: ignore
    password: constr(min_length=8) # type: ignore

    @root_validator(skip_on_failure=True)
    def at_least_one_contact(cls, values):
        email, phone = values.get('email'), values.get('phone')
        if not email and not phone:
            raise ValueError('Either email or phone must be provided.')
        return values
    @validator('password')
    def strong_password(cls, v):
        if not any(char.isupper() for char in v):
           raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char in "!@#$%^&*()_+" for char in v):
            raise ValueError('Password must contain at least one special character (!@#$%^&*()_+)')
        return v


class UserUpdate(BaseModel):
    first_name: Optional[constr(min_length=1, max_length=50)] = None # type: ignore
    last_name: Optional[constr(min_length=1, max_length=50)] = None # type: ignore
    phone: Optional[constr(min_length=10, max_length=15)] = None # type: ignore
    role: Optional[Role] = None 
    password: Optional[constr(min_length=8)] = None # type: ignore
    password_confirm: Optional[constr(min_length=8)] = None  # Password confirmation field # type: ignore
    current_password: Optional[constr(min_length=8)] = None  # Current password for validation # type: ignore
    two_factor_enabled: Optional[bool] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    is_suspended: Optional[bool] = None
    kyc_status: Optional[KYCStatus] = None

    @validator('password_confirm')
    def password_match(cls, v, values):
        if 'password' in values and values['password'] != v:
            raise ValueError('Passwords do not match')
        return v
class UserAdminUpdate(BaseModel):
    first_name: Optional[constr(min_length=1, max_length=50)] = None # type: ignore
    last_name: Optional[constr(min_length=1, max_length=50)] = None # type: ignore
    phone: Optional[constr(min_length=10, max_length=15)] = None # type: ignore
    email: Optional[EmailStr] = None
# Changed from EmailStr to str because some users may register with phone-only accounts.
# In those cases, we generate a temporary/fake email (e.g., phone_+251911111111_xxxxx@example.com)
# which may not pass strict RFC-compliant email validation used by EmailStr.
# Using str allows returning these temporary emails without causing serialization errors.
class UserOut(BaseModel):
    user_id: int
    email: Optional[str] = None 
    phone: Optional[str] = None
    role:Optional[Role] = Role.user
    is_active: bool
    is_verified: bool
    kyc_status: KYCStatus
    user_weekly_limit: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    kyc_document: Optional[KYCDocumentUser] = None
    profile_picture: Optional[str] = None
class UserList(BaseModel):
    kyc_document: Optional[KYCDocumentUser] = None
class UserProfile(BaseModel):
    user_id: int
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    is_flagged: Optional[bool] = None
    kyc_document: Optional[KYCDocumentUser] = None
    profile_picture: Optional[str] = None

class UserProfileUpdate(BaseModel):
    user_id: int
    email: Optional[EmailStr] = None
    phone: Optional[str] = None   
    profile_picture: Optional[str] = None
    class Config:
        from_attributes = True
    

class UserLogin(BaseModel):
    login_id: str = Field(..., description="Enter your phone number or email address here.")
    password: str = Field(..., description="Enter your password.")

    class Config:
        schema_extra = {
            "example": {
                "login_id": "user@example.com",
                "password": "examplepassword",
            }
        }

class Token(BaseModel):
    access_token: str    
    refresh_token: str
    token_type: str
    message: str


class AdminUserUpdate(BaseModel):
    kyc_status: Optional[str] = None  # "approved" or "rejected"
    user_weekly_limit: Optional[float] = None
    is_flagged: Optional[bool] = None
    admin_notes: Optional[str] = None

class TokenData(BaseModel):
    user_id: Optional[int] = None
class RefreshTokenRequest(BaseModel):
    refresh_token: str