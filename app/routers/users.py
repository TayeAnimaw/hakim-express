from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.core.security import verify_email_verified
from app.database.database import get_db
from app.models.users import User
from app.schemas.users import UserOut, UserUpdate,UserProfile,UserProfileUpdate
from passlib.context import CryptContext
from datetime import datetime, timedelta
from app.core.config import settings
from app.security import create_access_token, JWTBearer, get_password_hash, verify_access_token, verify_password # You already use this for login
from app.utils.email_service import normalize_email, send_email_async  # You used this in registration
import os
from app.security import get_current_user  
from typing import Optional
from app.models.kyc_documents import KYCDocument
from fastapi import Request



router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

import shutil

@router.post("/upload-profile-picture", response_model=UserProfile)
async def upload_profile_picture(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.user_id == current_user.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Save new file
    upload_dir = "uploads/profile_pictures"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{user.user_id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    # Remove old file if present
    if user.profile_picture and os.path.exists(user.profile_picture):
        try:
            os.remove(user.profile_picture)
        except Exception:
            pass
    user.profile_picture = file_path
    db.commit()
    db.refresh(user)
    return user

@router.put("/update-profile-picture", response_model=UserProfile)
async def update_profile_picture(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.user_id == current_user.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Remove old file if present
    if user.profile_picture and os.path.exists(user.profile_picture):
        try:
            os.remove(user.profile_picture)
        except Exception:
            pass
    # Save new file
    upload_dir = "uploads/profile_pictures"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{user.user_id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    user.profile_picture = file_path
    db.commit()
    db.refresh(user)
    return user

@router.get("/view-profile-picture", response_model=UserProfileUpdate)
def get_profile_picture(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    user = db.query(User).filter(User.user_id == current_user.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Construct the public URL if profile_picture exists
    profile_picture_url = None
    if user.profile_picture:
        # Normalize path for URL
        filename = os.path.basename(user.profile_picture)
        profile_picture_url = str(request.base_url) + f"uploads/{filename}"
    return {
        "user_id": user.user_id,
        "email": user.email,
        "phone": user.phone,
        "profile_picture": profile_picture_url
    }



# Change password securely
@router.put("/change-password")
async def change_password(
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_user = db.query(User).filter(User.user_id == current_user.user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(current_password, db_user.password):
        raise HTTPException(status_code=400, detail="Incorrect current password")

    if new_password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    db_user.password = get_password_hash(new_password)
    db.commit()
    db.refresh(db_user)

    return {"message": "Password changed successfully"}

# Forgot password (reset password flow via email)
@router.post("/forgot-password")
async def forgot_password(email: str, db: Session = Depends(get_db)):
    # email is not case sensitive
    email = normalize_email(email)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate a temporary reset token valid for 15 minutes
    reset_token = create_access_token(
        data={"sub": str(user.user_id)},
        expires_delta=timedelta(minutes=15)
    )

    # Send email with reset link
    # reset_link = f"https://hakim-express-admin.vercel.app/reset-password?token=%7BRESET_TOKEN%7D?token={reset_token}"
    reset_link = f"https://hakim-express-admin.vercel.app/reset-password?token={reset_token}"
    subject = "Reset Your Password"
    body = f"""
    Hi {user.email},

    We received a request to reset your password.
    Click the link below to reset it:

    {reset_link}

    This link will expire in 15 minutes.

    If you did not request this, you can safely ignore this email.

    Regards,
    Your App Support
    """
    await send_email_async(subject, user.email, body)

    return {"message": "Password reset link sent to your email"}

@router.post("/reset-password")
def reset_password(
    token: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    payload = verify_access_token(token)
    user_id = int(payload.get("sub"))

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if new_password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    user.password = get_password_hash(new_password)
    db.commit()
    db.refresh(user)

    return {"message": "Password reset successful"}
@router.put("/update-your-profile", response_model=UserProfile)
async def update_user_profile(
    email: Optional[str] = None,
    is_flagged: Optional[bool] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    selfie_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.user_id == current_user.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update User model fields
    if email is not None:
        # email is not case senstive
        email = normalize_email(email)
        user.email = email
    if is_flagged is not None:
        user.is_flagged = is_flagged

    # Update KYCDocument if exists
    kyc_doc = db.query(KYCDocument).filter(KYCDocument.user_id == user.user_id).first()
    if kyc_doc:
        if first_name is not None:
            kyc_doc.first_name = first_name
        if last_name is not None:
            kyc_doc.last_name = last_name
        if selfie_image is not None:
            # save file and store path (basic logic here, customize as needed)
            file_location = f"uploads/kyc_docs/{user.user_id}_{selfie_image.filename}"
            with open(file_location, "wb+") as file_object:
                file_object.write(await selfie_image.read())
            kyc_doc.selfie_image = file_location
    else:
        raise HTTPException(status_code=404, detail="KYC Document not found")

    db.commit()
    db.refresh(user)

    return user
