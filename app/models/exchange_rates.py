#app/models/exchange_rates.py
# -*- coding: utf-8 -*-
from sqlalchemy import Column, BigInteger, String, DECIMAL, Enum, Boolean, TIMESTAMP, Float
from app.database.database import Base
from datetime import datetime


class ExchangeRate(Base):
    __tablename__ = 'exchange_rates'
    exchange_rate_id = Column(BigInteger, primary_key=True, index=True)
    from_currency = Column(String(10), nullable=False)
    to_currency = Column(String(10), nullable=False)
     # For live exchange rate table
    bank_name = Column(String(255), nullable=True)
    buying_rate = Column(Float, nullable=True)
    selling_rate = Column(Float, nullable=True)
    rate = Column(DECIMAL(18, 6), nullable=True)
    available_balance_from = Column(DECIMAL(18, 2), default=490.43, nullable=True)
    available_balance_to = Column(DECIMAL(18, 2), default=90.43, nullable=True)   
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
