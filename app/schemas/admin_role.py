# app/schemas/admin_role.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# -------- AdminPermission Schemas --------
class AdminPermissionBase(BaseModel):
    permission: str

class AdminPermissionCreate(AdminPermissionBase):
    pass

class AdminPermissionResponse(AdminPermissionBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


# -------- AdminActivity Schemas --------
class AdminActivityBase(BaseModel):
    activity: str

class AdminActivityCreate(AdminActivityBase):
    pass

class AdminActivityResponse(AdminActivityBase):
    id: int
    timestamp: datetime
    admin_name: str
    pages_accessed: List[str]
    is_active: bool

    class Config:
        orm_mode = True


# -------- Admin Schema --------
class AdminBase(BaseModel):
    user_id: int

class AdminCreate(AdminBase):
    permissions: List[AdminPermissionCreate] = []

class AdminResponse(AdminBase):
    id: int
    created_at: datetime
    permissions: List[AdminPermissionResponse]

    class Config:
        orm_mode = True
# In app/models/admin_role.py or similar
class AdminPermissions:
    VIEW_USERS = "Can view users"
    APPROVE_KYC = "Can approve/reject KYC"
    EDIT_USER_PROFILE = "Can edit user profile info"
    SET_USER_LIMITS = "Can set user daily/weekly limits"
    SUSPEND_USERS = "Can suspend or unsuspend users"
    FLAG_USERS = "Can flag users (add internal notes)"
    EDIT_ADMIN_PERMS = "Can edit admin permissions"
    # Add others from UI
    
    @classmethod
    def all(cls):
        return [v for k,v in vars(cls).items() if not k.startswith('_')]