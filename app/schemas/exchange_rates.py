from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ExchangeRateBase(BaseModel):
    from_currency: str = Field(..., max_length=10)
    to_currency: str = Field(..., max_length=10)
    bank_name: Optional[str] = None
    buying_rate: Optional[float] = None
    selling_rate: Optional[float] = None
    rate: Optional[float] = None
    available_balance_from: Optional[float] = Field(default=490.43, description="Available balance in the from currency")
    available_balance_to: Optional[float] = Field(default=90.43, description="Available balance in the to currency")
    
class ExchangeRateCreate(ExchangeRateBase):
    pass
class ExchangeRateResponse(ExchangeRateBase):
    exchange_rate_id: int    
    created_at: datetime
    updated_at: datetime
class UserExchangeRateResponse(BaseModel):
    exchange_rate_id: int
    bank_name: Optional[str] = None
    buying_rate: Optional[float] = None
    selling_rate: Optional[float] = None
    rate: Optional[float] = None

class ConvertAmountResponse(BaseModel):
    original_amount: float
    converted_amount: float
    stripe_fee: float
    service_fee: float
    margin: float
    final_service_charge: float
    final_amount: float

    model_config = {
        "from_attributes": True
    }
