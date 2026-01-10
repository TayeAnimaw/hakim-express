from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.country import Country
from app.schemas.country import CountryCreate, CountryResponse
from typing import List

router = APIRouter()

# @router.post("/", response_model=CountryResponse, status_code=status.HTTP_201_CREATED)
# def create_country(country: CountryCreate, db: Session = Depends(get_db)):
#     db_country = db.query(Country).filter((Country.name == country.name) | (Country.code == country.code)).first()
#     if db_country:
#         raise HTTPException(status_code=400, detail="Country with this name or code already exists")
#     new_country = Country(name=country.name, code=country.code)
#     db.add(new_country)
#     db.commit()
#     db.refresh(new_country)
#     return new_country

@router.get("", response_model=List[CountryResponse])
def get_countries(db: Session = Depends(get_db)):
    countries = db.query(Country).all()
    return countries
