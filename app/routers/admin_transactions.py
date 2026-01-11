# app/routers/admin_transaction_fees.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from app.database.database import get_db
from app.models.transactions import Transaction, TransactionStatus
from app.models.manual_deposits import ManualDeposit

from app.schemas.transactions import TransactionUpdate, TransactionResponse
from app.security import JWTBearer, get_current_user
from app.models.users import User, Role
from app.models.payment_cards import PaymentCard
from app.models.notifications import Notification, ChannelType

router = APIRouter()

@router.get("", response_model=List[TransactionResponse])
def get_all_transactions(
    status: Optional[TransactionStatus] = Query(None),
    user_id: Optional[int] = Query(None),    
    amount: Optional[Decimal] = Query(None), 
    currency: Optional[str] = Query(None),     
    order: str = Query("newest", enum=["newest", "oldest"]),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    token: dict = Depends(JWTBearer()),
):
    try:
        current_user = get_current_user(db, token)
        if current_user.role != Role.admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

        # Start with base query including relationships
        query = db.query(Transaction).options(
            joinedload(Transaction.user).joinedload(User.kyc_document),
            joinedload(Transaction.payment_card)
        )

        # Apply filters
        query = query.filter(Transaction.amount > 0)
        if user_id:
            query = query.filter(Transaction.user_id == user_id )
        if status:
            query = query.filter(Transaction.status == status)    
        if currency:
            query = query.filter(Transaction.currency == currency)    
        if start_date:
            query = query.filter(Transaction.created_at >= start_date)
        if end_date:
            query = query.filter(Transaction.created_at <= end_date)

        # Apply ordering
        if order == "newest":
            query = query.order_by(Transaction.created_at.desc())
        else:
            query = query.order_by(Transaction.created_at.asc())

        # Apply pagination
        transactions = query.offset((page - 1) * per_page).limit(per_page).all()

        return transactions
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while fetching transactions try again")

@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction_details(
    transaction_id: int,
    db: Session = Depends(get_db),
    token: dict = Depends(JWTBearer()),
):
    try:
        current_user = get_current_user(db, token)
        if current_user.role != Role.admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

        transaction = db.query(Transaction).options(
            joinedload(Transaction.user).joinedload(User.kyc_document),
            joinedload(Transaction.payment_card)
        ).filter(Transaction.transaction_id == transaction_id,Transaction.amount > 0).first()
        if not transaction or transaction.amount <= 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

        return transaction
    except:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while fetching transactions try again")

@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction_status(
    transaction_id: int,
    data: TransactionUpdate,
    db: Session = Depends(get_db),
    token: dict = Depends(JWTBearer()),
):
    try:
        current_user = get_current_user(db, token)
        if current_user.role != Role.admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

        transaction = db.query(Transaction).options(
            joinedload(Transaction.user).joinedload(User.kyc_document),
            joinedload(Transaction.payment_card)
        ).filter(Transaction.transaction_id == transaction_id,Transaction.amount > 0).first()
        # transaction = transaction.filter(Transaction.amount > 0)
        if not transaction:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

        # Track old values
        old_status = transaction.status
        old_is_manual = transaction.is_manual

        # Update only provided fields
        for field, value in data.dict(exclude_unset=True).items():
            setattr(transaction, field, value)

        # Automatically set completed_at if status is changed to COMPLETED
        if data.status == TransactionStatus.completed and not transaction.completed_at:
            transaction.completed_at = datetime.utcnow()

        db.commit()

        # 🔁 Check if we need to create a ManualDeposit

        create_manual_deposit = False

        if data.status == TransactionStatus.failed and old_status != TransactionStatus.failed:
            create_manual_deposit = True

        if "is_manual" in data.dict(exclude_unset=True) and data.is_manual is True and not old_is_manual:
            create_manual_deposit = True

        if create_manual_deposit:
            if not transaction_id:
                raise HTTPException(status_code=400, detail="Transaction ID is missing")

            existing_deposit = db.query(ManualDeposit).filter(ManualDeposit.transaction_id == transaction_id).first()

            if not existing_deposit:
                try:
                    new_deposit = ManualDeposit(transaction_id=transaction_id)
                    db.add(new_deposit)
                    db.commit()
                except Exception as e:
                    db.rollback()
                    raise HTTPException(status_code=500, detail=f"Failed to create ManualDeposit: {str(e)}")

        # Return updated transaction
        updated_transaction = db.query(Transaction).options(
            joinedload(Transaction.user).joinedload(User.kyc_document),
            joinedload(Transaction.payment_card)
        ).filter(Transaction.transaction_id == transaction_id).first()

        # Notify all admin users
        admin_users = db.query(User).filter(User.role == Role.admin).all()
        for user in admin_users:
            notification = Notification(
                user_id=user.user_id,
                title="Transaction Status Updated",
                message=f"Transaction status were updated by {current_user.email or 'an admin'}",
                channel=ChannelType.push,
                type="transaction_fees_update",
                is_sent=True,
                sent_at=datetime.utcnow()
            )
            db.add(notification)

        db.commit()

        return updated_transaction
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred try again")

@router.get("/{user_id}/limits")
def get_user_transaction_limits(
    user_id: int,
    db: Session = Depends(get_db),
    token: dict = Depends(JWTBearer()),
):
    try:
        current_user = get_current_user(db, token)
        if current_user.role != Role.admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

        user = db.query(User).filter_by(user_id=user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        return {
            "weekly_limit": user.user_weekly_limit
        }
    except:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred try again")
@router.delete("/{transaction_id}", status_code=status.HTTP_200_OK)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    token: dict = Depends(JWTBearer()),
):
    try:
        current_user = get_current_user(db, token)
        if current_user.role != Role.admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

        transaction = db.query(Transaction).filter(Transaction.transaction_id == transaction_id,Transaction.amount > 0).first()
        # transaction = transaction.filter(Transaction.amount > 0)
        if not transaction:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

        # Optionally delete related ManualDeposit if it exists
        manual_deposit = db.query(ManualDeposit).filter(ManualDeposit.transaction_id == transaction_id).first()
        if manual_deposit:
            db.delete(manual_deposit)

        db.delete(transaction)
        db.commit()
        
        return {"message": "Transaction is deleted successfully"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred try again")
