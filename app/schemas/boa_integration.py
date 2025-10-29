# app/schemas/boa_integration.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from decimal import Decimal

# Beneficiary Response Schema
class BoABeneficiaryResponse(BaseModel):
    customer_name: Optional[str] = Field(None, description="Beneficiary customer name")
    account_currency: Optional[str] = Field(None, description="Account currency")
    enquiry_status: Optional[str] = Field(None, description="Inquiry status")
    cached: Optional[bool] = Field(False, description="Whether result came from cache")

    class Config:
        from_attributes = True

# Transfer Request Schemas
class BoATransferRequest(BaseModel):
    transaction_id: int = Field(..., description="Internal transaction ID")
    amount: str = Field(..., description="Transfer amount")
    account_number: str = Field(..., description="Recipient account number")
    reference: str = Field(..., description="Transaction reference")

class BoAOtherBankTransferRequest(BaseModel):
    transaction_id: int = Field(..., description="Internal transaction ID")
    amount: str = Field(..., description="Transfer amount")
    bank_code: str = Field(..., description="Destination bank code")
    account_number: str = Field(..., description="Recipient account number")
    reference: str = Field(..., description="Transaction reference")
    receiver_name: str = Field(..., description="Receiver name")

class BoAMoneySendRequest(BaseModel):
    amount: str = Field(..., description="Transfer amount")
    remitter_name: str = Field(..., description="Remitter name")
    remitter_phone: str = Field(..., description="Remitter phone number")
    receiver_name: str = Field(..., description="Receiver name")
    receiver_address: str = Field(..., description="Receiver address")
    receiver_phone: str = Field(..., description="Receiver phone number")
    reference: str = Field(..., description="Transaction reference")
    secret_code: str = Field(..., description="Secret code for transaction")

# Transfer Response Schema
class BoATransferResponse(BaseModel):
    success: bool = Field(..., description="Whether transfer was successful")
    boa_reference: Optional[str] = Field(None, description="BoA transaction reference")
    unique_identifier: Optional[str] = Field(None, description="Unique transaction identifier")
    transaction_status: Optional[str] = Field(None, description="Transaction status")
    response: Optional[Dict[str, Any]] = Field(None, description="Full BoA API response")

    class Config:
        from_attributes = True

# Status Response Schema
class BoAStatusResponse(BaseModel):
    id: Optional[str] = Field(None, description="Transaction ID")
    boa_reference: Optional[str] = Field(None, description="BoA reference")
    status: Optional[str] = Field(None, description="Transaction status")

    class Config:
        from_attributes = True

# Currency Rate Response Schema
class BoACurrencyRateResponse(BaseModel):
    currency_code: Optional[str] = Field(None, description="Currency code")
    currency_name: Optional[str] = Field(None, description="Currency name")
    buy_rate: Optional[Decimal] = Field(None, description="Buy rate")
    sell_rate: Optional[Decimal] = Field(None, description="Sell rate")

    class Config:
        from_attributes = True

# Balance Response Schema
class BoABalanceResponse(BaseModel):
    account_currency: Optional[str] = Field(None, description="Account currency")
    balance: Optional[Decimal] = Field(None, description="Account balance")

    class Config:
        from_attributes = True

# Bank List Response Schema
class BoABankListResponse(BaseModel):
    bank_id: str = Field(..., description="Bank ID")
    institution_name: str = Field(..., description="Bank name")

    class Config:
        from_attributes = True

# Error Response Schema
class BoAErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

# Webhook Schema for BoA status updates (if needed in future)
class BoAWebhookPayload(BaseModel):
    transaction_id: str = Field(..., description="BoA transaction ID")
    status: str = Field(..., description="Transaction status")
    reference: Optional[str] = Field(None, description="Transaction reference")
    timestamp: Optional[str] = Field(None, description="Status update timestamp")
    additional_data: Optional[Dict[str, Any]] = Field(None, description="Additional data")

# Request validation schemas for admin operations
class BoARefreshBankListRequest(BaseModel):
    force_refresh: Optional[bool] = Field(False, description="Force refresh even if recently updated")

class BoATestConnectionRequest(BaseModel):
    test_authentication: Optional[bool] = Field(True, description="Test OAuth authentication")
    test_transfer: Optional[bool] = Field(False, description="Test transfer endpoint")