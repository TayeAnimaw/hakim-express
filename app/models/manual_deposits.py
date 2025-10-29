# app/models/manual_deposits
from sqlalchemy import Column, BigInteger, Boolean, ForeignKey, Text, TIMESTAMP, String
from sqlalchemy.orm import relationship
from app.database.database import Base
from datetime import datetime

class ManualDeposit(Base):
    __tablename__ = "manual_deposits"

    id = Column(BigInteger, primary_key=True, index=True)
    transaction_id = Column(BigInteger, ForeignKey("transactions.transaction_id", ondelete="CASCADE"), nullable=False)
    note = Column(Text, nullable=True)
    completed = Column(Boolean, default=False)
    deposit_proof_image = Column(String, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    transaction = relationship("Transaction", back_populates="manual_deposits")
