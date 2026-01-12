from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload  # ✅ added joinedload
from typing import List
from datetime import datetime

from app.database.database import get_db
from app.models.kyc_documents import KYCDocument, KYCStatus
from app.models.users import User, Role
from app.schemas.kyc_documents import KYCDocumentOut
from app.security import JWTBearer, get_current_user
from pydantic import BaseModel

router = APIRouter()


# Admin role check
def require_admin(
    db: Session = Depends(get_db),
    token: dict = Depends(JWTBearer()),) -> User:
    # always token pass in header part not in url format 
    user = get_current_user(db,token)
    if user.role not in [Role.admin, Role.finance_officer, Role.support]:
        raise HTTPException(status_code=403, detail="Not authorized")
    return user


# Schema for rejection reason
class RejectReason(BaseModel):
    reason: str


#  List all KYC submissions with user email & phone
@router.get("/submissions", response_model=List[KYCDocumentOut])
def list_kyc_submissions(
    db: Session = Depends(get_db),
    token : dict = Depends(JWTBearer()),
   
   ):
    _ = require_admin(db, token)
    return db.query(KYCDocument)\
             .options(joinedload(KYCDocument.user))\
             .order_by(KYCDocument.created_at.desc())\
             .all()


# View specific KYC submission by user_id with user email & phone
@router.get("/{user_id}", response_model=KYCDocumentOut)
def get_kyc_by_user(
    user_id: int,
    db: Session = Depends(get_db),
    token: dict = Depends(JWTBearer())
):
    _ = require_admin(db, token)
    kyc = db.query(KYCDocument)\
            .options(joinedload(KYCDocument.user))\
            .filter(KYCDocument.user_id == user_id)\
            .first()

    if not kyc:
        raise HTTPException(status_code=404, detail="KYC not found")
    return kyc


# Approve a KYC submission
@router.post("/{user_id}/approve")
def approve_kyc(
    user_id: int,
    db: Session = Depends(get_db),
    token: dict = Depends(JWTBearer())
):
    _ = require_admin(db, token)
    kyc = db.query(KYCDocument).filter(KYCDocument.user_id == user_id).first()
    if not kyc:
        raise HTTPException(status_code=404, detail="KYC not found")

    kyc.status = KYCStatus.approved
    kyc.rejection_reason = None
    kyc.verified_at = datetime.utcnow()

    user = db.query(User).filter(User.user_id == user_id).first()
    if user:
        user.kyc_status = KYCStatus.approved

    db.commit()
    return {"message": "KYC approved successfully"}


# Reject a KYC submission with a reason
@router.post("/{user_id}/reject")
def reject_kyc(
    user_id: int,
    payload: RejectReason,
    db: Session = Depends(get_db),
    token: dict = Depends(JWTBearer())
):
    _ = require_admin(db, token)
    kyc = db.query(KYCDocument).filter(KYCDocument.user_id == user_id).first()
    if not kyc:
        raise HTTPException(status_code=404, detail="KYC not found")
    kyc.status = KYCStatus.rejected
    kyc.rejection_reason = payload.reason
    kyc.verified_at = datetime.utcnow()
    user = db.query(User).filter(User.user_id == user_id).first()
    if user:
        user.kyc_status = KYCStatus.rejected
    db.commit()
    return {
        "message": "KYC rejected successfully",
        "reason": payload.reason
    }


# Delete a user and their KYC document
@router.delete("/{user_id}/delete")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    token: dict = Depends(JWTBearer())
):
    _ = require_admin(db, token)
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    kyc = db.query(KYCDocument).filter(KYCDocument.user_id == user_id).first()
    if kyc:
        db.delete(kyc)

    db.delete(user)
    db.commit()

    return {"message": "User and their KYC document deleted successfully"}
