# File: app/admin.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.models.users import User, Role
from app.schemas.users import UserOut, UserUpdate, AdminUserUpdate, UserAdminUpdate
from app.database.database import get_db
from app.security import JWTBearer, get_current_user, check_permission
from datetime import datetime

from app.utils.email_service import normalize_email

router = APIRouter()

@router.get("/users", response_model=list[UserOut])
def get_users(
    db: Session = Depends(get_db),
    token: dict = Depends(JWTBearer())
    # current_user: User = Depends(check_permission("Can view users"))  # Correct usage
):
    """
    Retrieve all users (Admin only)
    
    Returns:
    - List of users with their KYC documents
    """
    current_user = get_current_user(db, token)
    if current_user.role != Role.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return db.query(User).options(joinedload(User.kyc_document)).all()    

@router.put("/users/{user_id}/manage", response_model=UserOut, summary="Manage user settings")
def admin_manage_user(
    user_id: int,
    user_update: AdminUserUpdate,
    db: Session = Depends(get_db),
    token: dict = Depends(JWTBearer())
    # current_user: User = Depends(check_permission("Can edit user profile info"))  # Example with different permission
):
    """
    Admin management of user account
    
    Updates:
    - KYC status (approved/rejected)
    - Weekly limit amount
    - Admin notes
    """
    current_user = get_current_user(db, token)
    if current_user.role != Role.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    user = db.query(User).options(
        joinedload(User.kyc_document)
    ).filter(User.user_id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update fields if they are provided
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    try:
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )

@router.put("/users/{user_id}", response_model=UserOut, summary="Update user profile")
def update_user(
    user_id: int,
    user_update: UserAdminUpdate,
    db: Session = Depends(get_db),
    token: dict = Depends(JWTBearer())
):
    """
    Update user profile information (Admin only)
    
    Can update:
    - First name (in KYC document)
    - Last name (in KYC document)
    - Phone number
    - Email address
    """
    current_user = get_current_user(db, token)
    # normalize email because email is not case sensitive
    if(not user_update.email):
        user_update.email = normalize_email(user_update.email)
    if current_user.role != Role.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    user = db.query(User).options(
        joinedload(User.kyc_document)
    ).filter(User.user_id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update user fields
    if user_update.phone is not None:
        user.phone = user_update.phone
    if user_update.email is not None:
        user.email = user_update.email

    # Update KYC document if exists
    if user.kyc_document:
        if user_update.first_name is not None:
            user.kyc_document.first_name = user_update.first_name
        if user_update.last_name is not None:
            user.kyc_document.last_name = user_update.last_name

    try:
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete user")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    token: dict = Depends(JWTBearer())
):
    """
    Delete a user account (Admin only)
    
    Warning: This action is irreversible
    """
    current_user = get_current_user(db, token)
    if current_user.role != Role.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    if current_user.user_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    try:
        db.delete(user)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )