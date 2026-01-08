# app/routers/admin_exchange_rates.py

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.database.database import get_db
from app.models.exchange_rates import ExchangeRate
from app.schemas.exchange_rates import (
    ExchangeRateCreate,
    ExchangeRateResponse,
    ConvertAmountResponse
)
from app.models.transaction_fees import TransactionFees
from app.schemas.transaction_fees import (
    TransactionFeesResponse,
    TransactionFeesUpdate
)
from app.security import JWTBearer, get_current_user
from app.models.users import User, Role

router = APIRouter()


def admin_required(current_user: User = Depends(get_current_user)):
    if current_user.role != Role.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


@router.post("/", response_model=ExchangeRateResponse)
def create_exchange_rate(
    data: ExchangeRateCreate,
    db: Session = Depends(get_db),
    token: dict = Depends(JWTBearer()),
):
    user = get_current_user(db,token)
    if user.role not in [Role.admin, Role.finance_officer, Role.support]:
        raise HTTPException(status_code=403, detail="Not authorized")
    exchange_rate = ExchangeRate(**data.dict())
    db.add(exchange_rate)
    db.commit()
    db.refresh(exchange_rate)
    return exchange_rate


@router.get("/", response_model=List[ExchangeRateResponse])
def get_all_exchange_rates(
    db: Session = Depends(get_db),
    token: dict = Depends(JWTBearer()),
):
    user = get_current_user(db,token)
    if user.role not in [Role.admin, Role.finance_officer, Role.support]:
        raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(ExchangeRate).order_by(ExchangeRate.created_at.desc()).all()


@router.delete("/{exchange_rate_id}")
def delete_exchange_rate(
    exchange_rate_id: int,
    db: Session = Depends(get_db),
    token: dict = Depends(JWTBearer()),
):
    user = get_current_user(db,token)
    if user.role not in [Role.admin, Role.finance_officer, Role.support]:
        raise HTTPException(status_code=403, detail="Not authorized")
    exchange_rate = db.query(ExchangeRate).filter_by(exchange_rate_id=exchange_rate_id).first()
    if not exchange_rate:
        raise HTTPException(status_code=404, detail="Exchange rate not found")

    db.delete(exchange_rate)
    db.commit()
    return {"detail": "Exchange rate deleted successfully"}

@router.get("/convert", response_model=ConvertAmountResponse)
def convert_amount(
    amount: float,
    from_currency: str,
    to_currency: str,
    db: Session = Depends(get_db),
    token: dict = Depends(JWTBearer())
):
    # Get exchange rate
    user = get_current_user(db,token)
    if user.role not in [Role.admin, Role.finance_officer, Role.support]:
        raise HTTPException(status_code=403, detail="Not authorized")
    rate = db.query(ExchangeRate).filter_by(
        from_currency=from_currency,
        to_currency=to_currency,
        is_active=True
    ).first()
    
    if not rate:
        raise HTTPException(status_code=404, detail="Exchange rate not found")
    
    # Get global transaction fees
    fees = db.query(TransactionFees).filter_by(is_active=True).first()
    if not fees:
        fees = TransactionFees()  # Use defaults
    
    converted = amount * rate.rate
    stripe_fee = (fees.stripe_fee / 100) * converted
    service_fee = (fees.service_fee / 100) * converted
    margin = (fees.margin / 100) * converted
    final_amount = converted - (stripe_fee + service_fee + margin)
    
    return ConvertAmountResponse(
        original_amount=amount,
        converted_amount=converted,
        stripe_fee=stripe_fee,
        service_fee=service_fee,
        margin=margin,
        final_amount=final_amount
    )