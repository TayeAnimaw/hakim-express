# app/schemas/transaction_fees.py
from pydantic import BaseModel,validator
from datetime import datetime

class TransactionFeesBase(BaseModel):
    stripe_fee: float = 2.9
    service_fee: float = 1.0
    margin: float = 2.0
    is_active: bool = True
    @validator('stripe_fee', 'service_fee', 'margin')
    def validate_fees(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Fees must be between 0 and 100')
        return v
    @property
    def final_service_charge(self):
        return self.stripe_fee + self.service_fee + self.margin

class TransactionFeesCreate(TransactionFeesBase):
    pass
class TransactionFeesUpdate(TransactionFeesBase):
    pass
class TransactionFeesResponse(TransactionFeesBase):
    id: int
    final_service_charge: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True