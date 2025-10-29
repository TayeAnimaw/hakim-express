# app/seeders.py
from sqlalchemy.orm import Session
from app.models.users import User, Role
from app.schemas.users import UserCreate
from app.security import get_password_hash  # Make sure to create a hashing utility

def create_admin_user(db: Session):
    # Check if there is already an admin user
    admin_user = db.query(User).filter(User.role == Role.admin).first()
    if not admin_user:
        # Admin doesn't exist, create one
        admin_data = UserCreate(
            email="admin@taye.com",
            phone="0912345678",
            password="SecurePassword123!"  # Make sure to set a strong password
        )
        
        # Hash the password before saving
        hashed_password = get_password_hash(admin_data.password)
        
        admin_user = User(
            email=admin_data.email,
            phone=admin_data.phone,
            password=hashed_password,
            role=Role.admin,
            is_verified=True,
            is_active=True
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        print("Admin user created.")
    else:
        print("Admin user already exists.")
