# app/routers/user_exchange_rate.py
from fastapi import APIRouter, HTTPException, Depends, status
from decimal import Decimal
from sqlalchemy.orm import Session
from typing import List

from app.database.database import get_db
from app.models.exchange_rates import ExchangeRate
from app.schemas.exchange_rates import ExchangeRateResponse, UserExchangeRateResponse
from app.models.exchange_rates import ExchangeRate
from app.schemas.exchange_rates import (
    ExchangeRateCreate,
    ExchangeRateResponse,
    ConvertAmountResponse
)
from app.models.transaction_fees import TransactionFees

from app.security import get_current_user
from app.models.users import User, Role
from app.models.transactions import Transaction, TransactionStatus
from sqlalchemy.orm import Session
from app.database.database import get_db



router = APIRouter()


@router.get("/", response_model=List[UserExchangeRateResponse])
def get_all_exchange_rates(db: Session = Depends(get_db)):
    return db.query(ExchangeRate).all()
@router.get("/all-live-exchange-rates", response_model=List[ExchangeRateResponse])
def get_all_exchange_rates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(ExchangeRate).order_by(ExchangeRate.created_at.desc()).all()
@router.get("/available-balance", response_model=dict)
def get_user_stripe_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get user's Stripe balance information including current balance and growth percentage.
    Returns data in a format suitable for displaying as a balance insight card.
    """
    # Get successful transactions
    successful_transactions = db.query(Transaction)\
        .filter(
            Transaction.user_id == current_user.user_id,
            # Add any additional filters for successful transactions here
        ).all()

    # Calculate total amount
    total_amount = sum(t.amount + (t.transfer_fee or Decimal(0)) for t in successful_transactions)
    
    # For demonstration, using a fixed growth percentage - you might calculate this based on previous period
    growth_percentage = 4.3  # In a real app, this would be calculated from historical data

    return {
        "title": "Insight",
        "current_balance": round(total_amount, 2),
        "currency": "birr",  
        "growth_percentage": growth_percentage,
        
    }


