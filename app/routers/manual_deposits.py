from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from fastapi import UploadFile, File, Form
from app.database.database import get_db
from app.models.manual_deposits import ManualDeposit
from app.models.transactions import Transaction, TransactionStatus
from app.models.users import User, Role
from app.schemas.manual_deposits import ManualDepositResponse, ManualDepositUpdate, ManualDepositResponseList
from app.security import JWTBearer, get_current_user
from datetime import datetime
from app.models.notifications import Notification, ChannelType

import os
import shutil

router = APIRouter()
UPLOAD_DIR = "uploads/deposit_proofs"
@router.get("", response_model=List[ManualDepositResponseList])
def list_failed_manual_deposits(
    db: Session = Depends(get_db), 
    token: dict = Depends(JWTBearer())):
    current_user = get_current_user(db, token)
    if current_user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Only admins can access this")

    deposits = (
        db.query(ManualDeposit)
        .join(Transaction)
        .options(joinedload(ManualDeposit.transaction).joinedload(Transaction.user))        
        .all()
    )

    # manually attach user since it's accessed via transaction → user
    for deposit in deposits:
        deposit.user = deposit.transaction.user

    return deposits

@router.put("/{deposit_id}", response_model=ManualDepositResponse)
def update_manual_deposit(
    deposit_id: int,
    note: Optional[str] = Form(None),
    completed: Optional[bool] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    token: dict = Depends(JWTBearer())
):
    current_user = get_current_user(db, token)
    if current_user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Only admins can update this")

    deposit = db.query(ManualDeposit).filter(ManualDeposit.id == deposit_id).first()
    if not deposit:
        raise HTTPException(status_code=404, detail="Manual deposit not found")

    # Handle file upload
    if file:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        filename = f"{deposit_id}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        deposit.deposit_proof_image = f"/uploads/deposit_proofs/{filename}"  # store as public URL

    # Update note and completed
    if note is not None:
        deposit.note = note
    if completed is not None:
        deposit.completed = completed
        if completed:
            transaction = db.query(Transaction).filter(Transaction.transaction_id == deposit.transaction_id).first()
            if transaction:
                transaction.status = TransactionStatus.completed
                if not transaction.completed_at:
                    transaction.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(deposit)

    # Ensure user is attached for response schema
    deposit.user = deposit.transaction.user
     # ✅ Create notification for the user
    if completed:
        user = deposit.transaction.user
        notification = Notification(
            user_id=user.user_id,
            title="Manual Deposit Approved",
            message=f"Your failed Transaction request with ID #{deposit.transaction_id} has been approved and processed successfully.",
            channel=ChannelType.push,  # or email/sms depending on your preference
            type="deposit_update",
            is_sent=True,  # Set to True if you don't have sending logic yet
            sent_at=datetime.utcnow()
        )
        db.add(notification)
        db.commit()

    return deposit
from fastapi import status

@router.delete("/{deposit_id}", status_code=status.HTTP_200_OK)
def delete_manual_deposit(
    deposit_id: int,
    db: Session = Depends(get_db),
    token : dict = Depends(JWTBearer())
):
    current_user = get_current_user(db, token)
    if current_user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Only admins can delete manual deposits")

    deposit = db.query(ManualDeposit).filter(ManualDeposit.id == deposit_id).first()

    if not deposit:
        raise HTTPException(status_code=404, detail="Manual deposit not found")

    # Delete related transaction first (if it exists)
    transaction = db.query(Transaction).filter(Transaction.transaction_id == deposit.transaction_id).first()
    if transaction:
        db.delete(transaction)

    # Delete deposit proof image if exists
    if deposit.deposit_proof_image:
        file_path = deposit.deposit_proof_image.lstrip("/")  # remove leading slash
        if os.path.exists(file_path):
            os.remove(file_path)

    db.delete(deposit)
    db.commit()

    return {"message": "Manual deposit and its related transaction deleted successfully"}
