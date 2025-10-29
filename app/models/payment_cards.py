# app/models/payment_cards.py
from sqlalchemy import Column, BigInteger, String, ForeignKey, Boolean, TIMESTAMP, Enum, UniqueConstraint, Integer
from sqlalchemy.orm import relationship, validates
from app.database.database import Base
from datetime import datetime
import re
import enum

class CardType(enum.Enum):
    
    VISA = "VISA"
    MASTER_CARD = "MASTER_CARD"
    AMERICAN_EXPRESS = "AMERICAN_EXPRESS"
    DISCOVER = "DISCOVER"
    PAYONEER = "PAYONEER"
    OTHER = "OTHER"

class PaymentCard(Base):
    __tablename__ = 'payment_cards'
    __table_args__ = (
    )

    payment_card_id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id', ondelete="CASCADE"), nullable=False)
    card_type = Column(Enum(CardType), nullable=False)
    stripe_payment_method_id = Column(String(255), nullable=True)  
    stripe_customer_id = Column(String(255), nullable=True) 
    brand = Column(String (50), nullable=True)  # e.g., VISA, MasterCard
    last4 = Column(String(4) , nullable=True)
    exp_month = Column(Integer , nullable=True)
    exp_year = Column(Integer , nullable=True)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)       
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship('User', back_populates='payment_cards')
    transactions = relationship('Transaction', back_populates='payment_card', cascade="all, delete-orphan")

    @validates('last4')
    def validate_last4(self, key, value):
        if not re.match(r'^\d{4}$', value):
            raise ValueError("Last four digits must be a 4-digit number.")
        return value

    @validates('exp_month', 'exp_year')
    def validate_expiry(self, key, value):
        if key == 'exp_month' and not (1 <= value <= 12):
            raise ValueError("Expiration month must be between 1 and 12.")
        if key == 'exp_year' and value < datetime.now().year:
           raise ValueError("Expiration year must not be in the past.")
        return value
    @property
    def display_name(self):
        """Formatted card display name (e.g., 'VISA •••• 4242')"""
        return f"{self.card_type.value} •••• {self.last4}"

    def __repr__(self):
        return f"<PaymentCard {self.payment_card_id} ({self.display_name})>"