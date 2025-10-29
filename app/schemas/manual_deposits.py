# app/schemas/manual_deposits.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.schemas.users import UserOut, UserList  # Assuming UserOut and UserList are defined in app/schemas/users.py
from app.schemas.transactions import TransactionDepotsit 

class ManualDepositBase(BaseModel):
    note: Optional[str] = None
    completed: Optional[bool] = False
    deposit_proof_image: Optional[str] = None

class ManualDepositCreate(ManualDepositBase):
    transaction_id: int

class ManualDepositUpdate(ManualDepositBase):
    pass

class ManualDepositResponse(ManualDepositBase):
    id: int
    transaction_id: int
    created_at: datetime
    updated_at: datetime
    user: Optional[UserOut] = None  # Assuming UserOut is defined in app/schemas/users.py
    transaction:Optional[TransactionDepotsit] = None  # Assuming you want to include transaction ID
class ManualDepositResponseList(BaseModel):
    id: int
    transaction:Optional[TransactionDepotsit] = None 
    user: Optional[UserList] = None  

    class Config:
        from_attributes = True
