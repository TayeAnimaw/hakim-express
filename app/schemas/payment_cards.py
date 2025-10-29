from pydantic import BaseModel, Field, field_validator, model_validator
from fastapi import Form
from datetime import datetime
from typing import Optional
import re
from enum import Enum
from app.schemas.users import UserBase  # Assuming you have a UserBase schema defined


class CardType(str, Enum):
    VISA = "VISA"
    MASTER_CARD = "MASTER_CARD"
    AMERICAN_EXPRESS = "AMERICAN_EXPRESS"
    DISCOVER = "DISCOVER"
    PAYONEER = "PAYONEER"
    OTHER = "OTHER"


# Simulated external store (Replace this with DB logic)
existing_last_four_digits = {"1234"}


class PaymentCardBase(BaseModel):
    card_type: CardType
    is_default: bool = False


class PaymentCardCreate(PaymentCardBase):
    stripe_payment_method_id: str


class PaymentCardUpdate(BaseModel):
    card_type: Optional[CardType]
    is_default: Optional[bool]
class CardBrand(BaseModel):
    brand: Optional[str] = None    

class PaymentCardResponse(PaymentCardBase):
    payment_card_id: int
    brand: Optional[str]
    last4: Optional[str]
    exp_month: Optional[int]
    exp_year: Optional[int]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    user: UserBase
    class Config:
        from_attributes = True  # Use this instead of orm_mode
        use_enum_values = True
