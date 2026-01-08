from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.transaction_fees import TransactionFees
from app.schemas.transaction_fees import TransactionFeesResponse
from typing import Dict

router = APIRouter()

@router.get("/", response_model=Dict[str, float])
def get_user_transaction_fees(
    db: Session = Depends(get_db)):
    fees = db.query(TransactionFees).filter_by(is_active=True).first()
    if not fees:
        # Default values if not set in DB
        stripe_fee = 2.9
        service_fee = 1.0
    else:
        stripe_fee = fees.stripe_fee
        service_fee = fees.service_fee
    total_transfer_fee = stripe_fee + service_fee
    return {
        # "stripe_fee": stripe_fee,
        # "service_fee": service_fee,
        "transfer_fee": total_transfer_fee
    }
