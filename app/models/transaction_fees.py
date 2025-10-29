# app/models/transaction_fees.py
from sqlalchemy import Column, Float, Boolean, TIMESTAMP, BigInteger
from app.database.database import Base
from datetime import datetime

class TransactionFees(Base):
    __tablename__ = 'transaction_fees'
    
    id = Column(BigInteger, primary_key=True, index=True)
    stripe_fee = Column(Float, default=2.9)  # 2.9% as shown in image
    service_fee = Column(Float, default=1.0)  # 1% as shown in image
    margin = Column(Float, default=2.0)  # 2% as shown in image
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    @property
    def final_service_charge(self):
        return self.stripe_fee + self.service_fee + self.margin