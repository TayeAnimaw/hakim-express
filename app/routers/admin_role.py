# app/routers/admin_role.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database.database import get_db
from app.models.admin_role import AdminRole, AdminActivity, AdminPermission
from app.models.users import User, Role
from app.security import JWTBearer, get_current_user, get_current_admin_user
from app.schemas.users import UserOut
from app.utils.utils import extract_pages_from_activity
from app.schemas.admin_role import AdminResponse, AdminActivityResponse, AdminActivityCreate, AdminPermissionCreate, AdminCreate

router = APIRouter()

@router.post("/assign-permissions/{user_id}", response_model=AdminResponse)
def assign_permissions(
    user_id: int,
    permissions: List[AdminPermissionCreate],
    db: Session = Depends(get_db),
    token: dict = Depends(JWTBearer()),
):
    user = get_current_user(db,token)
    if user.role not in [Role.admin, Role.finance_officer, Role.support]:
        raise HTTPException(status_code=403, detail="Not authorized")
   
    admin_role = db.query(AdminRole).filter(AdminRole.user_id == user_id).first()
    if not admin_role:
        admin_role = AdminRole(user_id=user_id)
        db.add(admin_role)
        db.commit()
        db.refresh(admin_role)

    for perm in permissions:
        db.add(AdminPermission(admin_id=admin_role.id, permission=perm.permission))
    db.commit()
    db.refresh(admin_role)
    return admin_role
@router.get("/activity-logs", response_model=List[AdminActivityResponse])
def get_activity_logs(
    db: Session = Depends(get_db),
    token: dict = Depends(JWTBearer()),
):
    user = get_current_user(db,token)
    if user.role not in [Role.admin, Role.finance_officer, Role.support]:
        raise HTTPException(status_code=403, detail="Not authorized")
    current_admin = get_current_admin_user(user)
    logs = db.query(AdminActivity).join(AdminRole).join(User).all()
    result = []

    for log in logs:
        result.append(AdminActivityResponse(
            id=log.id,
            activity=log.activity,
            timestamp=log.timestamp,
            admin_name=f"{log.admin.user.kyc_document.first_name} {log.admin.user.kyc_document.last_name}"
            if log.admin and log.admin.user and log.admin.user.kyc_document else "Unknown",
            pages_accessed=extract_pages_from_activity(log.activity),
            is_active=True
        ))

    return result
@router.put("/toggle-admin/{user_id}", response_model=UserOut)
def toggle_admin_status(
    user_id: int,
    db: Session = Depends(get_db),
    token: dict = Depends(JWTBearer()),
):
    admin_user = get_current_user(db,token)
    if admin_user.role not in [Role.admin, Role.finance_officer, Role.support]:
        raise HTTPException(status_code=403, detail="Not authorized")
    current_admin = get_current_admin_user(admin_user)
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role == Role.admin:
        user.role = Role.user
        # Optionally, remove admin role and permissions
        admin_role = db.query(AdminRole).filter(AdminRole.user_id == user_id).first()
        if admin_role:
            db.query(AdminPermission).filter(AdminPermission.admin_id == admin_role.id).delete()
            db.delete(admin_role)
    else:
        user.role = Role.admin
        # Optionally, create admin role
        admin_role = AdminRole(user_id=user_id)
        db.add(admin_role)

    db.commit()
    db.refresh(user)
    return user
