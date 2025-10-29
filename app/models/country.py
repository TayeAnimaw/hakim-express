from sqlalchemy import Column, BigInteger, String
from app.database.database import Base

class Country(Base):
    __tablename__ = 'countries'

    country_id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    code = Column(String(10), nullable=False, unique=True)
