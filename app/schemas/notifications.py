from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
from enum import Enum as PyEnum

class ChannelType(str, PyEnum):
    email = "email"
    sms = "sms"
    push = "push"

class NotificationBase(BaseModel):
    
    title: str
    message: str
    channel: ChannelType
    type: str
    doc_metadata: Optional[Any] = None

class NotificationCreate(NotificationBase):
    user_id: int

class NotificationOut(NotificationBase):
    notification_id: int
    user_id: int
    is_sent: bool
    sent_at: Optional[datetime] = None
    is_read: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }