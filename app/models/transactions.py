# app/models/transactions.py
from sqlalchemy import Column, BigInteger, String, ForeignKey, DECIMAL, Text, Enum, TIMESTAMP, Boolean,Numeric
from sqlalchemy.orm import relationship
from app.database.database import Base
from datetime import datetime
import enum

# Enums
class TransactionStatus(enum.Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"
    active = "active"

class AccountType(enum.Enum):
    bank_account = "bank_account"
    telebirr = "telebirr"

class Transaction(Base):
    __tablename__ = 'transactions'

    transaction_id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id', ondelete="CASCADE"), nullable=False)
    payment_card_id = Column(BigInteger, ForeignKey('payment_cards.payment_card_id', ondelete="CASCADE"), nullable=True)
    stripe_charge_id = Column(String(255), nullable=True)
    transaction_reference = Column(String(255), nullable=True)
    amount = Column(DECIMAL(18, 2), nullable=False)
    currency = Column(String(10), default="ETB")
    status = Column(Enum(TransactionStatus), default=TransactionStatus.pending)
    admin_note = Column(Text, nullable=True)
    is_manual = Column(Boolean, default=False)
    completed_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)    
    full_name = Column(String(100), default="Taye", nullable=True)
    account_type = Column(Enum(AccountType), nullable=True, default=AccountType.bank_account)
    bank_name = Column(String(100), nullable=True)
    account_number = Column(String(50), nullable=True)
    telebirr_number = Column(String(50), nullable=True)
    is_verified = Column(Boolean, default=False)
    transfer_fee = Column(Numeric(10, 2), nullable=True, default=3.2)
    # Manual card fields (for non-Stripe/manual cards)
    manual_card_number = Column(String(32), nullable=True)
    # manual_card_exp_month = Column(String(4), nullable=True)
    manual_card_exp_year = Column(String(8), nullable=True)
    manual_card_cvc = Column(String(8), nullable=True)
    manual_card_country = Column(String(32), nullable=True)
    manual_card_zip = Column(String(16), nullable=True)

    # Relationships
    user = relationship('User', back_populates='transactions')
    payment_card = relationship('PaymentCard', back_populates='transactions')
    manual_deposits = relationship('ManualDeposit', back_populates='transaction',cascade="all, delete-orphan",
    passive_deletes=True)
    boa_transaction = relationship('BoATransaction', back_populates='transaction', uselist=False, cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.status == TransactionStatus.completed and not self.completed_at:
            self.completed_at = datetime.utcnow()

    @property
    def sender_name(self):
        if not self.user or not self.user.kyc_document:
            return None
        return f"{self.user.kyc_document.first_name} {self.user.kyc_document.last_name}"

    @property
    def payment_method(self):
        return self.payment_card.card_type if self.payment_card else None
