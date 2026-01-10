from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.database import get_db
from app.models.recipients import Recipient
from app.models.users import User
from app.schemas.recipients import RecipientCreate, RecipientUpdate, RecipientResponse
from app.security import JWTBearer, get_current_user

router = APIRouter()


@router.post("", response_model=RecipientResponse)
def create_recipient(
    data: RecipientCreate,
    db: Session = Depends(get_db),
    token: dict = Depends(JWTBearer())
):
    current_user = get_current_user(db, token)
    # Check if recipient already exists for the user
    existing = db.query(Recipient).filter_by(phone=data.phone, user_id=current_user.user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Recipient with this phone already exists.")

    # Account type validation
    if data.account_type == "bank_account":
        if not data.bank_name or not data.account_number:
            raise HTTPException(status_code=400, detail="Bank name and account number are required for bank accounts.")
    elif data.account_type == "telebirr":
        if not data.telebirr_number:
            raise HTTPException(status_code=400, detail="Telebirr number is required for Telebirr.")

    recipient = Recipient(**data.dict(), user_id=current_user.user_id)
    db.add(recipient)
    db.commit()
    db.refresh(recipient)

    # Optional: load payment_cards via relationship if set
    recipient.payment_cards = current_user.payment_cards

    return recipient


@router.get("", response_model=List[RecipientResponse])
def get_all_recipients(
    db: Session = Depends(get_db),
    token: dict = Depends(JWTBearer())
):
    current_user = get_current_user(db, token)
    if current_user.role == "admin":
        return db.query(Recipient).all()
    return db.query(Recipient).filter_by(user_id=current_user.user_id).all()


@router.get("/{recipient_id}", response_model=RecipientResponse)
def get_recipient(
    recipient_id: int,
    db: Session = Depends(get_db),
    token: dict = Depends(JWTBearer())
):
    current_user = get_current_user(db, token)
    recipient = db.query(Recipient).filter_by(recipient_id=recipient_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")

    if current_user.role != "admin" and recipient.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Unauthorized to access this recipient")

    return recipient


@router.put("/{recipient_id}", response_model=RecipientResponse)
def update_recipient(
    recipient_id: int,
    data: RecipientUpdate,
    db: Session = Depends(get_db),
    token: dict = Depends(JWTBearer())
):
    current_user = get_current_user(db, token)
    recipient = db.query(Recipient).filter_by(recipient_id=recipient_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")

    if current_user.role != "admin" and recipient.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Unauthorized to update this recipient")

    update_data = data.dict(exclude_unset=True)

    # Validate fields if account_type is being updated
    if "account_type" in update_data:
        account_type = update_data["account_type"]
        if account_type == "bank_account":
            if not update_data.get("bank_name") or not update_data.get("account_number"):
                raise HTTPException(status_code=400, detail="bank_name and account_number are required for bank accounts.")
        elif account_type == "telebirr":
            if not update_data.get("telebirr_number"):
                raise HTTPException(status_code=400, detail="telebirr_number is required for Telebirr.")

    for key, value in update_data.items():
        setattr(recipient, key, value)

    db.commit()
    db.refresh(recipient)
    return recipient


@router.delete("/{recipient_id}")
def delete_recipient(
    recipient_id: int,
    db: Session = Depends(get_db),
    token: dict = Depends(JWTBearer())
):
    current_user = get_current_user(db, token)
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete recipients")

    recipient = db.query(Recipient).filter_by(recipient_id=recipient_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")

    db.delete(recipient)
    db.commit()
    return {"detail": "Recipient deleted successfully"}
