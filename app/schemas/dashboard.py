# app/schemas/dashboard.py
from pydantic import BaseModel
from datetime import date
from datetime import datetime
from typing import List, Optional
from app.schemas.kyc_documents import KYCDocumentUser  # or the appropriate Pydantic model

class MetricWithChange(BaseModel):
    value: float
    percentage_change: float
class SummaryMetrics(BaseModel):
    total_etb_disbursed: MetricWithChange
    total_transactions: MetricWithChange
    today_transactions: MetricWithChange
    pending_deposits: MetricWithChange
    total_users: MetricWithChange

class DailyTransaction(BaseModel):
    date: date
    amount: float


class DailyUserCount(BaseModel):
    date: date
    count: int

class UsersOverTimeResponse(BaseModel):
    today_total: int
    week_total: int
    percentage_change: float
    daily_counts: List[DailyUserCount]

class LatestTransaction(BaseModel):
    transaction_id: int
    reference: str    
    status: str
    amount: float
    # completed_at: Optional[datetime]
    created_at: Optional[datetime]
    currency: str  
    kyc_document: Optional[KYCDocumentUser] = None
    

    class Config:
        orm_mode = True
