from pydantic import BaseModel, Field

class CountryBase(BaseModel):
    name: str = Field(..., max_length=100, description="Country name")
    code: str = Field(..., max_length=10, description="Country code (e.g., 'ET', 'US')")

class CountryCreate(CountryBase):
    pass

class CountryResponse(CountryBase):
    country_id: int

    class Config:
        orm_mode = True
