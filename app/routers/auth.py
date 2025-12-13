# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Form
from typing import Optional
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from app.core.security import generate_random_otp, set_email_verified, store_verification_code, verify_code
from app.database.database import get_db
from app.models.admin_role import AdminPermission, AdminRole
from app.models.users import Role, User
from app.security import get_password_hash, verify_password
from app.core.config import settings
from typing import Annotated
from app.schemas.users import ReSendOTPRequest, Token, UserLogin, OTPVerify, UserCreate, UserOut, UserUpdate, RefreshTokenRequest
from app.utils.email_service import normalize_email, send_email_async
from fastapi import Body
from fastapi import Request
from jose import JWTError, jwt
from app.security import (
    authenticate_user,
    create_access_token,
    verify_access_token,
    get_current_user,
    JWTBearer,
    # ACCESS_TOKEN_EXPIRE_MINUTES,
    verify_password,
    get_password_hash,
    create_refresh_token      
)
import random

from app.utils.sms_service import send_sms
router = APIRouter()


@router.post("/login", response_model=Token)
async def login_for_access_token(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    # Check if user exists and authenticate user
    user = authenticate_user(db, login_data.login_id, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Credentials or incorrect username/password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if the user is active and verified
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
        )
    if not user.is_verified:
        # Send OTP if the user is not verified
        # to pass OTP we use hard coded only for test
        otp = "123456"
        # save the otp on redis
        await store_verification_code(login_data.login_id, otp)
        # This is where you send OTP to the user via email/SMS
        subject = "Verify Your OTP Code"
        body = f"Dear {user.email},\n\nYour OTP code is: {otp}\n\nIt will expire in 10 minutes.\n\nRegards,\nAdmin Taye"
        await send_email_async(subject, user.email, body)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your account is not verified. Please verify your OTP by entering the code sent to your email."
        )

    # Generate the access token for the user
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=7)
    access_token = create_access_token(
        data={"sub": str(user.user_id)},  # Using user_id as identifier
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
    data={"sub": str(user.user_id)},
    expires_delta=refresh_token_expires
   )

    # Update last login time
    user.last_login = datetime.utcnow()
    db.commit()
    
    return {
        "message": "You have successfully logged in.",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh-token", response_model=Token)
async def refresh_token(data: RefreshTokenRequest, db: Session = Depends(get_db)):
    refresh_token = data.refresh_token
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        user = db.query(User).filter(User.user_id == user_id).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        new_access_token = create_access_token(
            data={"sub": str(user.user_id)},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        return {
            "message": "Token refreshed successfully",
            "access_token": new_access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
# @router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
# async def create_user(
#     user_data: UserCreate,
#     db: Session = Depends(get_db)
# ):
#     # Ensure either email or phone is provided
#     if not user_data.email and not user_data.phone:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Either email or phone number must be provided."
#         )

#     # Check if verified email already exists
#     if user_data.email:
#         verified_email_user = db.query(User).filter(
#             User.email == user_data.email,
#             User.is_verified == True
#         ).first()
#         if verified_email_user:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Email already registered and verified."
#             )

#     # Check if verified phone already exists
#     if user_data.phone:
#         verified_phone_user = db.query(User).filter(
#             User.phone == user_data.phone,
#             User.is_verified == True
#         ).first()
#         if verified_phone_user:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Phone number already registered and verified."
#             )

#     try:
#         # Delete all unverified users with same email or phone
#         if user_data.email:
#             db.query(User).filter(
#                 User.email == user_data.email,
#                 User.is_verified == False
#             ).delete()

#         if user_data.phone:
#             db.query(User).filter(
#                 User.phone == user_data.phone,
#                 User.is_verified == False
#             ).delete()

#         # Generate OTP for verification
#         otp = generate_otp()
#         otp_expiry = datetime.utcnow() + timedelta(minutes=10)

#         # Create new user
#         db_user = User(
#             **user_data.dict(exclude={"password"}),
#             password=get_password_hash(user_data.password),
#             otp_code=otp,
#             otp_expires_at=otp_expiry,
#             is_verified=False,
#             created_at=datetime.utcnow(),
#             updated_at=datetime.utcnow()
#         )

#         db.add(db_user)
#         db.commit()
#         db.refresh(db_user)

#         # Send OTP to email if email is provided
#         if db_user.email:
#             subject = "Your OTP Code for Account Verification"
#             body = f"Hello {db_user.email},\n\nYour OTP code is: {otp}\n\nThis code will expire in 10 minutes.\n\nThank you!"
#             await send_email_async(subject, db_user.email, body)

#         return db_user

#     except Exception as e:
#         db.rollback()
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Could not create user: {str(e)}"
        # )
# @router.post("/verify-otp", response_model=Token)
# async def verify_otp(data: OTPVerify, db: Session = Depends(get_db)):
#     try:
#         # Start a new transaction
#         db.begin()
        
#         # Lock the user row for update to prevent race conditions
#         user = db.query(User).filter(User.email == data.email).with_for_update().first()
#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")

#         if user.is_verified:
#             # Generate and return token even if already verified
#             access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
#             access_token = create_access_token(
#                 data={"sub": str(user.user_id)},
#                 expires_delta=access_token_expires
#             )
#             refresh_token = create_refresh_token(
#                 data={"sub": str(user.user_id)},
#                 expires_delta=timedelta(days=7)
#             )
#             db.commit()  # Explicit commit
#             return {
#                 "message": "User already verified",
#                 "access_token": access_token,
#                 "refresh_token": refresh_token,
#                 "token_type": "bearer"
#             }

#         if user.otp_code != data.otp:
#             db.rollback()  # Explicit rollback
#             raise HTTPException(status_code=400, detail="Invalid OTP")

#         if datetime.utcnow() > user.otp_expires_at:
#             db.rollback()  # Explicit rollback
#             raise HTTPException(status_code=400, detail="OTP expired")

#         # Set user as verified and clear OTP fields
#         user.is_verified = True
#         user.otp_code = None
#         user.otp_expires_at = None
#         user.updated_at = datetime.utcnow()
        
#         # Generate tokens
#         access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
#         access_token = create_access_token(
#             data={"sub": str(user.user_id)},
#             expires_delta=access_token_expires
#         )
#         refresh_token = create_refresh_token(
#             data={"sub": str(user.user_id)},
#             expires_delta=timedelta(days=7)
#         )
        
#         db.commit()  # Explicit commit
        
#         return {
#             "message": "OTP verified successfully",
#             "access_token": access_token,
#             "refresh_token": refresh_token,
#             "token_type": "bearer"
#         }

#     except Exception as e:
#         db.rollback()  # Ensure rollback on any error
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Error verifying OTP: {str(e)}"
#         )
@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    # Ensure either email or phone is provided
    # email is not case sensitive
    if user_data.email:
        user_data.email = normalize_email(user_data.email)
    if not user_data.email and not user_data.phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either email or phone number must be provided."
        )

    # Check if verified email already exists
    if user_data.email:
        verified_email_user = db.query(User).filter(
            User.email == user_data.email,
            User.is_verified == True
        ).first()
        if verified_email_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered and verified."
            )

    # Check if verified phone already exists
    if user_data.phone:
        verified_phone_user = db.query(User).filter(
            User.phone == user_data.phone,
            User.is_verified == True
        ).first()
        if verified_phone_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered and verified."
            )

    try:
        # Delete all unverified users with same email or phone
        if user_data.email:
            db.query(User).filter(
                User.email == user_data.email,
                User.is_verified == False
            ).delete()

        if user_data.phone:
            db.query(User).filter(
                User.phone == user_data.phone,
                User.is_verified == False
            ).delete()

        # Generate a unique email for phone-only users
        user_email = user_data.email
        if not user_email and user_data.phone:
            import uuid
            unique_suffix = str(uuid.uuid4().hex)[:8]
            # Changed the temporary email domain from '@temp.local' to '@example.com'
            # because Pydantic v2 rejects '.local' domains as invalid email addresses.
            # '@example.com' is a safe, valid dummy domain for testing and auto-generated users.
            user_email = f"phone_{user_data.phone}_{unique_suffix}@example.com"

        # Determine OTP
        print(user_data.email, user_data.phone)
        if user_data.email:
            otp = generate_random_otp()
            # to pass OTP we use hard coded only for test
            # otp = "123456"
            # save the otp on redis
            await store_verification_code(user_data.email, otp)
        else:
    
            otp = generate_random_otp()
        
            
            # save the otp on redis by phone number
            await store_verification_code(user_data.phone, otp)

        # Create new user
        db_user = User(
            email=user_email,
            phone=user_data.phone,
            password=get_password_hash(user_data.password),
            is_verified=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        # Send OTP to email if email is provided (skip for generated temp emails)
        print(db_user)
        if user_data.email and not user_data.email.endswith('@temp.local'):
            subject = "Your OTP Code for Account Verification"
            body = f"Hello {db_user.email},\n\nYour OTP code is: {otp}\n\nThis code will expire in 10 minutes.\n\nThank you!"
            await send_email_async(subject, db_user.email, body)
        else:
            message = f"Hakim Express: Welcome! Your OTP is {otp}. Expires in 10 minutes. Complete your registration."
            send_sms(db_user.phone, message)

        return db_user

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not create user: {str(e)}"
        )
@router.post("/verify-otp", response_model=Token)
async def verify_otp(data: OTPVerify, db: Session = Depends(get_db)):
    try:
        db.begin()

        # Validate that either email or phone is provided
        if not data.email and not data.phone:
            raise HTTPException(status_code=400, detail="Email or phone number is required for verification.")
        # email is not case sensitive
        if data.email:
            data.email = normalize_email(data.email)
        # Retrieve user using email or phone
        query = db.query(User).with_for_update()
        if data.email:
            user = query.filter(User.email == data.email).first()
        else:
            user = query.filter(User.phone == data.phone).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.is_verified:
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": str(user.user_id)},
                expires_delta=access_token_expires
            )
            refresh_token = create_refresh_token(
                data={"sub": str(user.user_id)},
                expires_delta=timedelta(days=7)
            )
            db.commit()
            return {
                "message": "User already verified",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            }
        is_otp_valid = await verify_code(data.email if data.email else data.phone, data.otp)
        if not is_otp_valid:
            db.rollback()
            raise HTTPException(status_code=400, detail="Invalid OTP")

        # Mark user as verified
        # save email of phone who is recently validated otp
        await set_email_verified(data.email if data.email else data.phone)
        user.is_verified = True
        user.updated_at = datetime.utcnow()

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.user_id)},
            expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.user_id)},
            expires_delta=timedelta(days=7)
        )

        db.commit()

        return {
            "message": "OTP verified successfully",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error verifying OTP: {str(e)}"
        )

# @router.post("/resend-otp")
# async def resend_otp(
#     email: str = Body(..., embed=True),
#     db: Session = Depends(get_db)
# ):
#     # Check if user exists
#     user = db.query(User).filter(User.email == email).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     if user.is_verified:
#         return {"message": "User already verified"}

#     # Generate a new OTP and expiry time
#     otp = generate_otp()
#     otp_expiry = datetime.utcnow() + timedelta(minutes=10)

#     # Update user record
#     user.otp_code = otp
#     user.otp_expires_at = otp_expiry
#     db.commit()

#     # Send the new OTP to the user's email
#     subject = "Your New OTP Code for Verification"
#     body = f"Hi {user.email},\n\nYour new OTP code is: {otp}\nThis code will expire in 10 minutes.\n\nThanks!"
#     await send_email_async(subject, user.email, body)

#     return {"message": "A new OTP has been sent to your email"}

@router.post("/resend-otp")
async def resend_otp(
    data: ReSendOTPRequest,
    db: Session = Depends(get_db)
):
    if not data.email and not data.phone:
        raise HTTPException(status_code=400, detail="Email or phone is required.")
    # email is not case sensitive
    if data.email:
        data.email = normalize_email(data.email)
    # Query user by email or phone
    user = None
    if data.email:
        user = db.query(User).filter(User.email == data.email).first()
    elif data.phone:
        user = db.query(User).filter(User.phone == data.phone).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        return {"message": "User already verified"}

    # Refresh OTP and expiry
    if data.email:
        otp = generate_random_otp()
        # to pass OTP we use hard coded only for test
        # otp = "123456"
        # save the otp on redis
        await store_verification_code(data.email, otp)
        subject = "Your New OTP Code for Verification"
        body = f"Hi {user.email},\n\nYour new OTP code is: {otp}\nThis code will expire in 10 minutes.\n\nThanks!"
        await send_email_async(subject, user.email, body)
    else:
        otp = generate_random_otp()
        await store_verification_code(data.phone, otp)
        message = f"Hakim Express: You requested a new OTP. Your OTP is {otp} and it is valid for 10 minutes. \nDo not share this code with anyone."
        send_sms(data.phone, message)
        # No SMS sending since SMS provider is not configured

    return {
        "message": "A new OTP has been set. Check your contact method.",
        "otp_delivery": "email" if user.email else "phone"
    }

# Logout endpoint - invalidates the token at the client-side (handled on the client)
@router.post("/logout")
async def logout(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    return {"message": "Successfully logged out and token invalidated"}

@router.post("/create-admin", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_admin(user_data: UserCreate, db: Session = Depends(get_db)):
    # Ensure either email or phone is provided
    if not user_data.email and not user_data.phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either email or phone number must be provided."
        )
    # email is not case sensitive
    if user_data.email:
        user_data.email = normalize_email(user_data.email)
    # Check if verified email already exists
    if user_data.email:
        verified_email_user = db.query(User).filter(
            User.email == user_data.email,
            User.is_verified == True
        ).first()
        if verified_email_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered and verified."
            )

    # Check if verified phone already exists
    if user_data.phone:
        verified_phone_user = db.query(User).filter(
            User.phone == user_data.phone,
            User.is_verified == True
        ).first()
        if verified_phone_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered and verified."
            )

    # Delete all unverified users with same email or phone
    if user_data.email:
        db.query(User).filter(
            User.email == user_data.email,
            User.is_verified == False
        ).delete()
    if user_data.phone:
        db.query(User).filter(
            User.phone == user_data.phone,
            User.is_verified == False
        ).delete()

    # Generate a unique email for phone-only users
    user_email = user_data.email
    if not user_email and user_data.phone:
        import uuid
        unique_suffix = str(uuid.uuid4().hex)[:8]
        user_email = f"phone_{user_data.phone}_{unique_suffix}@example.com"
    # Create user as admin
    db_user = User(
        email=user_email,
        phone=user_data.phone,
        password=get_password_hash(user_data.password),
        role=Role.admin,
        is_verified=True,  # Admins auto-verified
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Create AdminRole entry
    admin_role = AdminRole(user_id=db_user.user_id)
    db.add(admin_role)
    db.commit()
    db.refresh(admin_role)

    # Assign default permissions
    default_perms = ["view_users", "edit_users", "toggle-admin", "activity-logs"]
    for perm in default_perms:
        db.add(AdminPermission(admin_id=admin_role.id, permission=perm))
    db.commit()

    return db_user
