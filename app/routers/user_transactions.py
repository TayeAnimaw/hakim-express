# app/routers/user_transactions.py
from fastapi import APIRouter, Depends, HTTPException, logger, status, Form
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime
from app.database.database import get_db
from app.models.transactions import Transaction, TransactionStatus
from app.schemas.transactions import TransactionCreate, TransactionResponse, AccountType, TransactionUpdate
from decimal import Decimal
from app.security import JWTBearer, get_current_user
from app.models.users import User, Role
from app.models.payment_cards import PaymentCard
import stripe
import os
from app.core.config import settings 
from app.models.notifications import Notification, ChannelType
from app.utils.boa_service import BoABeneficiaryService, BoAServiceError



router = APIRouter()
stripe.api_key = settings.STRIPE_SECRET_KEY
@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_user_transaction(
    amount: Decimal = Form(...),
    currency: str = Form("usd"),
    transaction_reference: Optional[str] = Form(...),
    payment_card_id: Optional[int] = Form(None),  
    full_name: str = Form(...),
    account_type: AccountType = Form(...),
    bank_name: Optional[str] = Form(None),
    account_number: Optional[str] = Form(None),
    telebirr_number: Optional[str] = Form(None),
    transfer_fee: Decimal=12.48,  # New field for transfer fee


    #  New fields for manual card entry
    card_number: Optional[str] = Form(None),   
    exp_year: Optional[int] = Form(None),
    exp_month: str = "12",  # Default to December
    cvc: Optional[str] = Form(None),
    zip: Optional[str] = Form(None),
    country: Optional[str] = Form(None),

    db: Session = Depends(get_db),
    token: dict = Depends(JWTBearer())
):
    """
    Create a new transaction using either a saved card or manual card entry.
    """

    # 🚫 Prevent admins from using this endpoint
    current_user = get_current_user(db, token)
    if current_user.role == Role.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins should use the admin API for transactions"
        )

    # Stripe setup
    # stripe_amount = int(amount * 100)
    total_amount = amount + transfer_fee
    stripe_amount = int(total_amount * 100)
    payment_method_id = None
    customer_id = None

    if payment_card_id:
        # ✅ Use saved card
        card = db.query(PaymentCard).filter(
            PaymentCard.payment_card_id == payment_card_id,
            PaymentCard.user_id == current_user.user_id
        ).first()

        if not card:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or unauthorized card."
            )

        payment_method_id = card.stripe_payment_method_id

        customer_id = card.stripe_customer_id
        

        # Stripe logic for saved card
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=stripe_amount,
                currency=currency.lower(),
                customer=customer_id,
                payment_method=payment_method_id,
                confirm=True,
                automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
                metadata={
                    "user_id": str(current_user.user_id),
                    "transaction_reference": transaction_reference,
                }
            )
            stripe_charge_id = payment_intent.id
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stripe payment failed: {e.user_message or str(e)}"
            )

        transaction = Transaction(
            amount=amount,
            transfer_fee=transfer_fee,
            currency=currency,
            transaction_reference=transaction_reference,
            payment_card_id=payment_card_id,
            stripe_charge_id=stripe_charge_id,
            full_name=full_name,
            account_type=account_type,
            bank_name=bank_name,
            account_number=account_number,
            telebirr_number=telebirr_number,
            user_id=current_user.user_id,
            status=TransactionStatus.pending
        )
    elif card_number:
        # ✅ Use manual card (not Stripe, just save info)
        transaction = Transaction(
            amount=amount,
            transfer_fee=transfer_fee,
            currency=currency,
            transaction_reference=transaction_reference,
            payment_card_id=None,
            stripe_charge_id=None,
            full_name=full_name,
            account_type=account_type,
            bank_name=bank_name,
            account_number=account_number,
            telebirr_number=telebirr_number,
            user_id=current_user.user_id,
            status=TransactionStatus.pending,
            is_manual=True,
            manual_card_number=card_number,
            # manual_card_exp_month=exp_month,
            manual_card_exp_year=exp_year,
            manual_card_cvc=cvc,
            manual_card_country=country,
            manual_card_zip=zip
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must provide either a payment_card_id or a manual card number."
        )

    try:
        db.add(transaction)

        # 5. Create Notification
        notification = Notification(
            user_id=current_user.user_id,
            title="Transaction Created",
            message=f"Your transaction with Amount: {amount} {currency} has been created and is pending.",
            channel=ChannelType.push,
            type="transaction_created",
            is_sent=True,
            sent_at=datetime.utcnow()
        )
        db.add(notification)

        db.commit()
        db.refresh(transaction)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transaction creation failed: {str(e)}"
        )

    return transaction

@router.post("/{transaction_id}/process-boa-transfer")
async def process_boa_transfer(
    transaction_id: int,
    db: Session = Depends(get_db),
    token: dict = Depends(JWTBearer())
):
    """
    Process a transaction through Bank of Abyssinia API
    """
    # Get the transaction
    current_user = get_current_user(db, token)
    transaction = db.query(Transaction).filter(
        Transaction.transaction_id == transaction_id,
        Transaction.user_id == current_user.user_id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    if transaction.status != TransactionStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction is not in pending status"
        )

    try:
        # Validate beneficiary if it's a bank transfer
        if transaction.account_type == AccountType.bank_account and transaction.account_number:
            beneficiary_result = await BoABeneficiaryService.fetch_beneficiary_name(
                transaction.account_number, db
            )

            if not beneficiary_result:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unable to verify beneficiary account"
                )

        # Process the transfer based on account type
        if transaction.account_type == AccountType.bank_account:
            # Within BoA transfer
            transfer_result = await BoABeneficiaryService.fetch_beneficiary_name(
                transaction.account_number, db
            )

            if transfer_result and transfer_result.get("account_currency") == "ETB":
                # This is a BoA account, use within BoA transfer
                from app.utils.boa_service import BoATransferService

                boa_result = await BoATransferService.initiate_within_boa_transfer(
                    transaction_id=transaction_id,
                    amount=str(transaction.amount),
                    account_number=transaction.account_number,
                    reference=transaction.transaction_reference or f"TXN{transaction_id}",
                    db=db
                )

                # Update transaction status
                transaction.status = TransactionStatus.completed
                transaction.completed_at = datetime.utcnow()

                # Create success notification
                notification = Notification(
                    user_id=current_user.user_id,
                    title="Transfer Completed",
                    message=f"Your transfer of {transaction.amount} {transaction.currency} to {beneficiary_result.get('customer_name', 'beneficiary')} has been completed successfully.",
                    channel=ChannelType.push,
                    type="transfer_completed",
                    is_sent=True,
                    sent_at=datetime.utcnow()
                )
                db.add(notification)

            else:
                # Other bank transfer - would need bank ID from user
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Other bank transfers require bank selection. Please contact support."
                )

        elif transaction.account_type == AccountType.telebirr:
            # For telebirr, we could integrate with mobile money APIs
            # For now, mark as completed (this would be replaced with actual API call)
            transaction.status = TransactionStatus.completed
            transaction.completed_at = datetime.utcnow()

            # Create success notification
            notification = Notification(
                user_id=current_user.user_id,
                title="Mobile Money Transfer Completed",
                message=f"Your mobile money transfer of {transaction.amount} {transaction.currency} has been completed successfully.",
                channel=ChannelType.push,
                type="transfer_completed",
                is_sent=True,
                sent_at=datetime.utcnow()
            )
            db.add(notification)

        db.commit()
        db.refresh(transaction)

        return {
            "message": "Transfer processed successfully",
            "transaction_id": transaction_id,
            "status": transaction.status.value,
            "completed_at": transaction.completed_at
        }

    except BoAServiceError as e:
        logger.error(f"BoA service error processing transfer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transfer processing failed: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing transfer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transfer processing failed: {str(e)}"
        )

@router.post("/{transaction_id}/validate-beneficiary")
async def validate_beneficiary(
    transaction_id: int,
    db: Session = Depends(get_db),
    token: dict = Depends(JWTBearer())
):
    """
    Validate beneficiary account before processing transfer
    """
    # Get the transaction
    current_user = get_current_user(db, token)
    transaction = db.query(Transaction).filter(
        Transaction.transaction_id == transaction_id,
        Transaction.user_id == current_user.user_id
    ).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    if not transaction.account_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No account number provided for validation"
        )

    try:
        # Validate beneficiary
        beneficiary_result = await BoABeneficiaryService.fetch_beneficiary_name(
            transaction.account_number, db
        )

        if not beneficiary_result:
            return {
                "valid": False,
                "message": "Unable to verify beneficiary account"
            }

        return {
            "valid": True,
            "customer_name": beneficiary_result.get("customer_name"),
            "account_currency": beneficiary_result.get("account_currency"),
            "message": "Beneficiary account verified successfully"
        }

    except BoAServiceError as e:
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Beneficiary validation failed: {str(e)}"
        )

@router.get("", response_model=List[TransactionResponse])
def get_user_transactions(
    db: Session = Depends(get_db),
    token: dict = Depends(JWTBearer())
):
    """
    Get all transactions for the authenticated user
    """
    current_user = get_current_user(db, token)
    return db.query(Transaction)\
        .options(joinedload(Transaction.payment_card))\
        .filter(Transaction.user_id == current_user.user_id)\
        .order_by(Transaction.created_at.desc())\
        .all()

@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_user_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    token: dict = Depends(JWTBearer())
):
    """
    Get specific transaction details for the authenticated user
    """
    current_user = get_current_user(db, token)
    transaction = db.query(Transaction)\
        .options(joinedload(Transaction.payment_card))\
        .filter(
            Transaction.transaction_id == transaction_id,
            Transaction.user_id == current_user.user_id
        )\
        .first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found or access denied"
        )

    return transaction
