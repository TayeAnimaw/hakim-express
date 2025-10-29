# app/schemas/kyc_documents.py
from pydantic import BaseModel
from datetime import date, datetime
from enum import Enum
from typing import Optional
from pydantic import validator

class GenderEnum(str, Enum):
    male = "male"
    female = "female"
    other = "other"

class IDTypeEnum(str, Enum):
    passport = "passport"
    national_id = "national_id"
    driver_license = "driver_license"

class KYCStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
# Add this to hold email and phone
class KycDocumentBase(BaseModel):
    first_name: str
    last_name: str
    dob: date
    street_name: Optional[str]
    house_no: Optional[str]
    additional_info: Optional[str]
    postal_code: Optional[str]
    region: Optional[str]
    city: Optional[str]
    country: Optional[str]
    gender: GenderEnum
class UserBasicOut(BaseModel):
    email: str
    phone: Optional[str] = None

    class Config:
        orm_mode = True

class KYCDocumentCreate(BaseModel):
    first_name: str
    last_name: str
    dob: date
    street_name: Optional[str]
    house_no: Optional[str]
    additional_info: Optional[str]
    postal_code: Optional[str]
    region: Optional[str]
    city: Optional[str]
    country: Optional[str]
    gender: GenderEnum

    id_type: IDTypeEnum
    front_image: str
    back_image: Optional[str] = None
    selfie_image: str

class KYCDocumentOut(KYCDocumentCreate):
    id: int
    user_id: int
    status: KYCStatus
    rejection_reason: Optional[str]
    verified_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    # Add nested user field
    user: Optional[UserBasicOut]
    @validator('dob', pre=True)
    def fix_invalid_dob(cls, value):
        if value in ('0000-00-00', None, ''):
            return None  # or return a default like date(1900, 1, 1)
        return value
class KYCDocumentUser(BaseModel):
    first_name: str
    last_name: str    

    class Config:        
        from_attributes = True  # Use this instead of orm_mode
        use_enum_values = True
