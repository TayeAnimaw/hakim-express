# File: app/routers/notifications.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database.database import get_db
from app.models.notifications import Notification
from app.schemas.notifications import NotificationCreate, NotificationOut
# File: app/routers/notifications.py
from app.models.users import User
from app.security import JWTBearer, get_current_user

router = APIRouter()

@router.get("", response_model=List[NotificationOut])
def get_notifications(
    db: Session = Depends(get_db),
    token: dict = Depends(JWTBearer())
):
    current_user = get_current_user(db, token)
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.user_id
    ).order_by(Notification.created_at.desc()).all()
    return notifications

# Get unread notification count for the logged-in user
@router.get("/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    token: dict = Depends(JWTBearer())
):
    current_user = get_current_user(db, token)
    count = db.query(Notification).filter(
        Notification.user_id == current_user.user_id,
        Notification.is_read == False
    ).count()
    return {"unread_count": count}

# Mark a notification as read by ID (only if it belongs to the user)
@router.patch("/mark-as-read/{notification_id}", response_model=NotificationOut)
def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    token: dict = Depends(JWTBearer())
):
    current_user = get_current_user(db, token)
    notification = db.query(Notification).filter(
        Notification.notification_id == notification_id,
        Notification.user_id == current_user.user_id
    ).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found or access denied")

    if notification.is_read:
        return notification  # Already marked

    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification