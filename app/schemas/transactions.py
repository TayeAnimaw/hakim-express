# app\schemas/transactions.py
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from enum import Enum
from datetime import datetime
from app.schemas.payment_cards import CardBrand, PaymentCardResponse
from app.schemas.users import UserBase

# Enum for Transaction Status
class TransactionStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"
    active = "active"
class AccountType(str, Enum):
    bank_account = "bank_account"
    telebirr = "telebirr"

# Base Schema
class TransactionBase(BaseModel):
    amount: Decimal = Field(..., gt=0,description="Amount associated with the recipient", example=100.0)
    currency: str =Field(default="ETB",max_length=10)    
    admin_note: Optional[str] =Field(None, max_length=500)
    is_manual: bool = Field(default=False)
    transaction_reference: Optional[str] = Field(..., min_length=5, max_length=255)
    payment_card_id: Optional[int] = None
    stripe_charge_id: Optional[str] = None
    full_name: Optional[str] = Field(None, description="Full name of the recipient")
    # phone: str = Field(..., description="Phone number of the recipient", example="+251912345678")
    account_type: AccountType = Field(..., description="Type of account: bank_account or telebirr")
    bank_name: Optional[str] = Field(None, description="Bank name (required if account_type is 'bank_account')", example="Commercial Bank of Ethiopia")
    account_number: Optional[str] = Field(None, description="Bank account number (required if account_type is 'bank_account')", example="1000123456789")
    telebirr_number: Optional[str] = Field(None, description="Telebirr number (required if account_type is 'telebirr')", example="0912345678")
    is_verified: Optional[bool] = Field(False, description="Verification status")
    # Manual card fields (for non-Stripe/manual cards)
    manual_card_number: Optional[str] = None
    manual_card_exp_month: Optional[str] = None
    manual_card_exp_year: Optional[str] = None
    manual_card_cvc: Optional[str] = None
    manual_card_country: Optional[str] = None
    manual_card_zip: Optional[str] = None

# For Creating
class TransactionCreate(BaseModel):
    pass

# For Internal Use
class TransactionInternal(TransactionBase):      
    status: TransactionStatus = TransactionStatus.pending

# For Updating
class TransactionUpdate(BaseModel):
    status: Optional[TransactionStatus] = None
    admin_note: Optional[str] =None
    completed_at: Optional[datetime] = None
    is_verified: Optional[bool] = None
    is_manual: Optional[bool] = None
    
class TransactionDepotsit(BaseModel):
    transaction_id: int
    amount: Decimal = Field(..., gt=0, description="Amount associated with the deposit", example=100.0)
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when the deposit was created")
    status: TransactionStatus = Field(default=TransactionStatus.pending, description="Status of the deposit")
    payment_card: Optional[CardBrand] = None
# Response
class TransactionResponse(TransactionInternal):
    transaction_id: int
    status: TransactionStatus      
    transaction_reference: str
    is_manual: bool
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    admin_note: Optional[str]
    transfer_fee: Optional[Decimal] = None
    payment_card: Optional[PaymentCardResponse] = None
    # Manual card fields (for non-Stripe/manual cards)
    manual_card_number: Optional[str] = None
    # manual_card_exp_month: Optional[str] = None
    manual_card_exp_year: Optional[str] = None
    manual_card_cvc: Optional[str] = None
    manual_card_country: Optional[str] = None
    manual_card_zip: Optional[str] = None
    # user: UserBase  # Nested user with email, phone, and kyc info
    class Config:
        from_attributes = True  # Use this instead of orm_mode
        use_enum_values = True
