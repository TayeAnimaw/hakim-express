# app/routers/contact_us.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.database import get_db
from app.models.contact_us import ContactUs
from app.schemas.contact_us import ContactUsCreate, ContactUsResponse
from app.security import get_current_user
from app.models.users import User, Role
from app.models.notifications import Notification, ChannelType
from datetime import datetime

router = APIRouter()

def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role not in [Role.admin, Role.finance_officer, Role.support]:
        raise HTTPException(status_code=403, detail="Not authorized")
    return user

# Anyone can post contact message
@router.post("/", response_model=ContactUsResponse)
def submit_contact_us(data: ContactUsCreate, db: Session = Depends(get_db)):
    contact = ContactUs(**data.dict())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    # Notify all admin users
    admin_users = db.query(User).filter(User.role == Role.admin).all()
    for user in admin_users:
        notification = Notification(
            user_id=user.user_id,
            title="contact message",
            message=f"New contact message from {contact.email} ",            
            channel=ChannelType.push,
            type="transaction_fees_update",
            is_sent=True,
            sent_at=datetime.utcnow()
        )
        db.add(notification)

    db.commit()
    return contact

#  Only admin can get all messages
@router.get("/", response_model=List[ContactUsResponse])
def get_all_messages(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    return db.query(ContactUs).order_by(ContactUs.created_at.desc()).all()

#  Only admin can delete a message
@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(
    contact_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    contact = db.query(ContactUs).filter(ContactUs.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact message not found")
    db.delete(contact)
    db.commit()
