from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.kyc_documents import KYCDocument, KYCStatus, IDTypeEnum, GenderEnum
from app.models.users import User
from app.schemas.kyc_documents import KYCDocumentOut
from app.security import get_current_user
from datetime import datetime
import shutil
import os
import uuid

router = APIRouter()

UPLOAD_DIR = "uploads/kyc_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_file(file: UploadFile, prefix: str) -> str:
    filename = f"{prefix}_{uuid.uuid4().hex}_{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return filepath

@router.post("/submit", response_model=KYCDocumentOut)
def submit_kyc(
    first_name: str = Form(...),
    last_name: str = Form(...),
    dob: str = Form(...,description="Date of birth in ISO format (YYYY-MM-DD)"),  # Use ISO format date: YYYY-MM-DD
    street_name: str = Form(None),
    house_no: str = Form(None),
    additional_info: str = Form(None),
    postal_code: str = Form(None),
    region: str = Form(None),
    city: str = Form(None),
    country: str = Form(None, description="Country name"),
    gender: GenderEnum = Form(...),
    id_type: IDTypeEnum = Form(...),
    front_image: UploadFile = File(...),
    back_image: UploadFile = File(None),
    selfie_image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user : User = Depends(get_current_user),
):
    try:
        print(f"Current user: {current_user.user_id}, is_verified: {current_user.is_verified}")
        if not current_user.is_verified:
            raise HTTPException(status_code=403, detail="User must verify OTP before submitting KYC")

        existing = db.query(KYCDocument).filter(KYCDocument.user_id == current_user.user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="KYC already submitted")
        try:
            dob_date = datetime.strptime(dob, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format for dob. Use YYYY-MM-DD.")


        front_path = save_file(front_image, "front")
        selfie_path = save_file(selfie_image, "selfie")
        back_path = save_file(back_image, "back") if back_image else None
        new_kyc = KYCDocument(
            user_id=current_user.user_id,
            first_name=first_name,
            last_name=last_name,
            dob=dob_date,
            street_name=street_name,
            house_no=house_no,
            additional_info=additional_info,
            postal_code=postal_code,
            region=region,
            city=city,
            country=country,
            gender=gender,
            id_type=id_type,
            front_image=front_path,
            back_image=back_path,
            selfie_image=selfie_path,
        )

        db.add(new_kyc)
        current_user.kyc_status = KYCStatus.pending
        db.commit()
        db.refresh(new_kyc)
        return new_kyc
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
from sqlalchemy.orm import joinedload

@router.get("/me", response_model=KYCDocumentOut)
def get_my_kyc(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    print(123)
    kyc = db.query(KYCDocument).options(joinedload(KYCDocument.user)).filter(
        KYCDocument.user_id == current_user.user_id
    ).first()

    if not kyc:
        raise HTTPException(status_code=404, detail="KYC document not found")

    # Debug logging
    print(f"Debug: kyc.user = {kyc.user}")
    if kyc.user:
        print(f"Debug: user.email = {kyc.user.email}, user.phone = {kyc.user.phone}, user.email type = {type(kyc.user.email)}")

        # Handle null email for existing users
        if kyc.user.email is None:
            kyc.user.email = ""
    print(kyc)
    return kyc

@router.put("/update", response_model=KYCDocumentOut)
def update_my_kyc(
    first_name: str = Form(None),
    last_name: str = Form(None),
    street_name: str = Form(None),
    house_no: str = Form(None),
    additional_info: str = Form(None),
    postal_code: str = Form(None),
    region: str = Form(None),
    city: str = Form(None),
    country: str = Form(None),
    gender: GenderEnum = Form(None),
    id_type: IDTypeEnum = Form(None),
    dob: str = Form(None, description="Date of birth in ISO format (YYYY-MM-DD)"),
    front_image: UploadFile = File(None),
    back_image: UploadFile = File(None),
    selfie_image: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    kyc = db.query(KYCDocument).filter(KYCDocument.user_id == current_user.user_id).first()
    if not kyc:
        raise HTTPException(status_code=404, detail="KYC document not found")
  
    if first_name is not None:
        kyc.first_name = first_name
    if last_name is not None:
        kyc.last_name = last_name
    if street_name is not None:
        kyc.street_name = street_name
    if house_no is not None:
        kyc.house_no = house_no
    if additional_info is not None:
        kyc.additional_info = additional_info
    if postal_code is not None:
        kyc.postal_code = postal_code
    if region is not None:
        kyc.region = region
    if city is not None:
        kyc.city = city
    if country is not None:
        kyc.country = country
    if gender is not None:
        kyc.gender = gender
    if id_type is not None:
        kyc.id_type = id_type
    if dob is not None:
        try:
            kyc.dob = datetime.strptime(dob, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format for dob. Use YYYY-MM-DD.")

    if front_image is not None:
        kyc.front_image = save_file(front_image, "front")

    if back_image is not None:
        kyc.back_image = save_file(back_image, "back")

    if selfie_image is not None:
        kyc.selfie_image = save_file(selfie_image, "selfie")

    db.commit()
    db.refresh(kyc)
    return kyc

@router.put("/selfie-image", response_model=KYCDocumentOut)
def update_selfie_image(
    selfie_image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Replace the selfie image of the authenticated user's KYC document.
    Users can only update their own selfie image.
    """
    kyc = db.query(KYCDocument).filter(KYCDocument.user_id == current_user.user_id).first()
    
    if not kyc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="KYC document not found for this user"
        )
    
    if kyc.status == KYCStatus.approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update selfie after KYC has been approved"
        )
    
    # Save new file
    selfie_path = save_file(selfie_image, "selfie")
    
    # Optionally delete old file if it exists
    if kyc.selfie_image and os.path.exists(kyc.selfie_image):
        try:
            os.remove(kyc.selfie_image)
        except OSError:
            pass  # Log this error in production
    
    # Update only the selfie_image field
    kyc.selfie_image = selfie_path
    kyc.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(kyc)
    
    return kyc