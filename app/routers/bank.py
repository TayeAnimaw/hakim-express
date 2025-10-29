from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.bank import Bank
from app.schemas.bank import BankCreate, BankResponse
from typing import List

router = APIRouter()

@router.post("/", response_model=BankResponse, status_code=status.HTTP_201_CREATED)
def create_bank(bank: BankCreate, db: Session = Depends(get_db)):
    db_bank = db.query(Bank).filter((Bank.bank_name == bank.bank_name) | (Bank.bank_code == bank.bank_code)).first()
    if db_bank:
        raise HTTPException(status_code=400, detail="Bank with this name or code already exists")
    new_bank = Bank(bank_name=bank.bank_name, bank_code=bank.bank_code)
    db.add(new_bank)
    db.commit()
    db.refresh(new_bank)
    return new_bank

@router.get("/", response_model=List[BankResponse])
def get_banks(db: Session = Depends(get_db)):
    banks = db.query(Bank).all()
    return banks
