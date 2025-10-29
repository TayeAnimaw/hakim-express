from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime
from app.schemas.users import UserBase

class AccountType(str, Enum):
    bank_account = "bank_account"
    telebirr = "telebirr"

class RecipientBase(BaseModel):
    full_name: str = Field(..., description="Full name of the recipient", example="John Doe")
    phone: str = Field(..., description="Phone number of the recipient", example="+251912345678")
    account_type: AccountType = Field(..., description="Type of account: bank_account or telebirr")
    bank_name: Optional[str] = Field(None, description="Bank name (required if account_type is 'bank_account')", example="Commercial Bank of Ethiopia")
    account_number: Optional[str] = Field(None, description="Bank account number (required if account_type is 'bank_account')", example="1000123456789")
    telebirr_number: Optional[str] = Field(None, description="Telebirr number (required if account_type is 'telebirr')", example="0912345678")
    is_verified: Optional[bool] = Field(False, description="Verification status")
    amount: Optional[float] = Field(0.0, description="Amount associated with the recipient", example=100.0)

class RecipientCreate(RecipientBase):
    pass

class RecipientUpdate(BaseModel):
    full_name: Optional[str] = Field(None, description="Full name of the recipient")
    phone: Optional[str] = Field(None, description="Phone number of the recipient")
    account_type: Optional[AccountType] = Field(None, description="Type of account")
    bank_name: Optional[str] = Field(None, description="Bank name (if applicable)")
    account_number: Optional[str] = Field(None, description="Bank account number (if applicable)")
    telebirr_number: Optional[str] = Field(None, description="Telebirr number (if applicable)")
    is_verified: Optional[bool] = Field(None, description="Verification status")

class RecipientResponse(RecipientBase):
    recipient_id: int
    created_at: datetime
    updated_at: datetime
    

    class Config:
        orm_mode = True
