from pydantic import BaseModel, Field

class BankBase(BaseModel):
    bank_name: str = Field(..., max_length=100, description="Bank name")
    bank_code: str = Field(..., max_length=20, description="Bank code (unique identifier)")

class BankCreate(BankBase):
    pass

class BankResponse(BankBase):
    bank_id: int

    class Config:
        from_attributes = True
