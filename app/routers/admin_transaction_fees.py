# app/routers/admin_transaction_fees.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.transaction_fees import TransactionFees
from app.schemas.transaction_fees import (
    TransactionFeesResponse,
    TransactionFeesUpdate
)
from app.security import get_current_user
from app.models.users import User, Role
from datetime import datetime
from app.models.notifications import Notification, ChannelType

router = APIRouter()

@router.get("/", response_model=TransactionFeesResponse)
def get_transaction_fees(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    fees = db.query(TransactionFees).filter_by(is_active=True).first()
    if not fees:
        fees = TransactionFees()
        db.add(fees)
        db.commit()
        db.refresh(fees)
    return fees

@router.put("/", response_model=TransactionFeesResponse)
def update_transaction_fees(
    data: TransactionFeesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    fees = db.query(TransactionFees).filter_by(is_active=True).first()
    if not fees:
        fees = TransactionFees(**data.dict())
        db.add(fees)
    else:
        for field, value in data.dict().items():
            setattr(fees, field, value)
    
    db.commit()
    db.refresh(fees)
    # Notify all admin users
    admin_users = db.query(User).filter(User.role == Role.admin).all()
    for user in admin_users:
        notification = Notification(
            user_id=user.user_id,
            title="Transaction Fees Updated",
            message=f"Transaction fees were updated by {current_user.email or 'an admin'}",
            channel=ChannelType.push,
            type="transaction_fees_update",
            is_sent=True,
            sent_at=datetime.utcnow()
        )
        db.add(notification)

    db.commit()

    return fees