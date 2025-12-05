# app/seeders.py
from sqlalchemy.orm import Session
from app.models.users import User, Role
from app.schemas.users import UserCreate
from app.security import get_password_hash
import os
from app.models.country import Country
from app.models.bank import Bank
from app.models.transaction_fees import TransactionFees
from app.models.exchange_rates import ExchangeRate


def create_admin_user(db: Session):
    # Check if there is already an admin user
    admin_user = db.query(User).filter(User.role == Role.admin).first()
    if not admin_user:
        # Get admin credentials from environment variables with defaults
        admin_email = os.getenv("ADMIN_EMAIL", "admin@taye.com")
        admin_phone = os.getenv("ADMIN_PHONE", "0912345678")
        admin_password = os.getenv("ADMIN_PASSWORD", "SecurePassword123!")

        # Admin doesn't exist, create one
        admin_data = UserCreate(
            email=admin_email,
            phone=admin_phone,
            password=admin_password
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
    else:
        print("Admin user already exists.")

def seed_countries(db: Session):
    if db.query(Country).count() == 0:
        countries = [
            Country(name="Ethiopia", code="ET"),
            Country(name="United States", code="US"),
            Country(name="United Kingdom", code="GB"),
            Country(name="Canada", code="CA"),
            Country(name="Kenya", code="KE"),
        ]
        db.add_all(countries)
        db.commit()
    else:
        print("Countries already exist.")

def seed_banks(db: Session):
    if db.query(Bank).count() == 0:
        banks = [
            Bank(bank_name="Commercial Bank of Ethiopia", bank_code="CBE"),
            Bank(bank_name="Awash Bank", bank_code="AWASH"),
            Bank(bank_name="Bank of Abyssinia", bank_code="BOA"),
            Bank(bank_name="Dashen Bank", bank_code="DASHEN"),
        ]
        db.add_all(banks)
        db.commit()
    else:
        print("Banks already exist.")

def seed_transaction_fees(db: Session):
    if not db.query(TransactionFees).first():
        fees = TransactionFees(stripe_fee=2.9, service_fee=1.0, margin=2.0, is_active=True)
        db.add(fees)
        db.commit()
    else:
        print("Transaction fees already exist.")

def seed_exchange_rates(db: Session):
    if db.query(ExchangeRate).count() == 0:
        rates = [
            ExchangeRate(from_currency="USD", to_currency="ETB", rate=55.0),
            ExchangeRate(from_currency="GBP", to_currency="ETB", rate=70.0),
            ExchangeRate(from_currency="EUR", to_currency="ETB", rate=65.0),
        ]
        db.add_all(rates)
        db.commit()
    else:
        print("Exchange rates already exist.")
