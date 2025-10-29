# app/models/boa_integration.py

from sqlalchemy import Column, BigInteger, String, ForeignKey, DECIMAL, Text, TIMESTAMP, Boolean, JSON
from sqlalchemy.orm import relationship
from app.database.database import Base
from datetime import datetime
import enum

# Enums for BoA-specific statuses
class BoATransactionStatus(enum.Enum):
    pending = "pending"
    live = "Live"
    success = "success"
    failed = "failed"
    timeout = "timeout"

class BoATransactionType(enum.Enum):
    within_boa = "within_boa"
    other_bank_ethswitch = "other_bank_ethswitch"
    money_send = "money_send"

class BoABeneficiaryStatus(enum.Enum):
    success = "success"
    failure = "failure"

class BoATransaction(Base):
    """Model for Bank of Abyssinia transactions"""
    __tablename__ = 'boa_transactions'

    id = Column(BigInteger, primary_key=True, index=True)
    transaction_id = Column(BigInteger, ForeignKey('transactions.transaction_id', ondelete="CASCADE"), nullable=False)

    # BoA-specific fields
    boa_reference = Column(String(100), nullable=True)  # BoA's unique reference like "FT23343L0Z8C"
    unique_identifier = Column(String(100), nullable=True)  # Like "IRFX240244833914396.00"
    infinity_reference = Column(String(100), nullable=True)

    # Transaction details
    transaction_type = Column(String(50), nullable=True)  # "AC" for account transfer
    boa_transaction_status = Column(String(20), default="pending")  # "Live", "success", "failed"

    # Financial details
    debit_account_id = Column(String(50), nullable=True)
    credit_account_id = Column(String(50), nullable=True)
    debit_amount = Column(DECIMAL(18, 2), nullable=True)
    credit_amount = Column(DECIMAL(18, 2), nullable=True)
    debit_currency = Column(String(10), default="ETB")
    credit_currency = Column(String(10), default="ETB")

    # Additional BoA response data
    reason = Column(String(255), nullable=True)
    transaction_date = Column(String(20), nullable=True)

    # Audit information from BoA
    audit_info = Column(JSON, nullable=True)  # T24_time, responseParse_time, etc.

    # Timestamps
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    transaction = relationship('Transaction', back_populates='boa_transaction')

class BoABeneficiaryInquiry(Base):
    """Model for beneficiary name inquiries"""
    __tablename__ = 'boa_beneficiary_inquiries'

    id = Column(BigInteger, primary_key=True, index=True)
    account_id = Column(String(50), nullable=False, index=True)
    bank_id = Column(String(20), nullable=True)  # For other bank inquiries

    # Response data
    customer_name = Column(String(200), nullable=True)
    account_currency = Column(String(10), nullable=True)
    enquiry_status = Column(String(10), nullable=True)  # "0" for failure, "1" for success

    # Metadata
    inquiry_type = Column(String(20), nullable=False)  # "boa" or "other_bank"
    boa_response = Column(JSON, nullable=True)  # Full BoA response

    # Timestamps
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    expires_at = Column(TIMESTAMP, nullable=True)  # Cache expiry

class BoABankList(Base):
    """Model for BoA bank list"""
    __tablename__ = 'boa_bank_list'

    id = Column(BigInteger, primary_key=True, index=True)
    bank_id = Column(String(20), nullable=False, unique=True, index=True)
    institution_name = Column(String(200), nullable=False)

    # Metadata
    is_active = Column(Boolean, default=True)
    last_updated = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

class BoACurrencyRate(Base):
    """Model for BoA currency rates"""
    __tablename__ = 'boa_currency_rates'

    id = Column(BigInteger, primary_key=True, index=True)
    currency_code = Column(String(10), nullable=False, index=True)
    currency_name = Column(String(50), nullable=True)

    # Rates
    buy_rate = Column(DECIMAL(18, 4), nullable=True)
    sell_rate = Column(DECIMAL(18, 4), nullable=True)

    # Metadata
    boa_response = Column(JSON, nullable=True)
    last_updated = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

class BoABalance(Base):
    """Model for BoA account balance"""
    __tablename__ = 'boa_balances'

    id = Column(BigInteger, primary_key=True, index=True)

    # Balance information
    account_currency = Column(String(10), nullable=True)
    balance = Column(DECIMAL(18, 2), nullable=True)

    # Metadata
    boa_response = Column(JSON, nullable=True)
    last_updated = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

# Update existing models to include BoA relationships

# Update Transaction model to include BoA relationship
def update_transaction_model():
    """Add BoA relationship to existing Transaction model"""
    from app.models.transactions import Transaction
    # This would be done via migration in a real scenario
    pass

# Update Bank model to include BoA-specific fields
def update_bank_model():
    """Add BoA-specific fields to existing Bank model"""
    from app.models.bank import Bank
    # This would be done via migration in a real scenario
    pass