from sqlalchemy import Column, BigInteger, String
from app.database.database import Base

class Bank(Base):
    __tablename__ = 'banks'

    bank_id = Column(BigInteger, primary_key=True, index=True)
    bank_name = Column(String(100), nullable=False, unique=True)
    bank_code = Column(String(20), nullable=False, unique=True)
