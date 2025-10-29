# app/schemas/contact_us.py
from pydantic import BaseModel, EmailStr
from datetime import datetime

class ContactUsBase(BaseModel):
    email: EmailStr
    message: str

class ContactUsCreate(ContactUsBase):
    pass

class ContactUsUpdate(BaseModel):
    email: EmailStr | None = None
    message: str | None = None

class ContactUsResponse(ContactUsBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
