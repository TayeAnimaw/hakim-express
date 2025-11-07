# app/schemas/boa_integration.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from decimal import Decimal

# Beneficiary Response Schema
class BoABeneficiaryResponse(BaseModel):
    """
    Response schema for beneficiary name inquiries.
    Used for both BOA and other bank account queries.    .
    """
    customer_name: Optional[str] = Field(None, description="Beneficiary customer name")
    account_currency: Optional[str] = Field(None, description="Account currency (e.g., 'ETB')")
    enquiry_status: Optional[str] = Field(None, description="Inquiry status - '1' for success, '0' for failure (other bank only)")
    cached: Optional[bool] = Field(False, description="Whether result came from cache")

    class Config:
        from_attributes = True

# Transfer Request Schemas
class BoATransferRequest(BaseModel):
    """
    Request schema for within-BOA transfers.
    """
    transaction_id: int = Field(..., description="Internal transaction ID for tracking")
    amount: str = Field(..., description="Transfer amount as string (e.g., '100.00')")
    account_number: str = Field(..., description="Recipient BOA account number")
    reference: str = Field(..., description="Unique transaction reference")

class BoAOtherBankTransferRequest(BaseModel):
    """
    Request schema for other bank transfers via EthSwitch.
    """
    transaction_id: int = Field(..., description="Internal transaction ID for tracking")
    amount: str = Field(..., description="Transfer amount as string")
    bank_code: str = Field(..., description="Destination bank code (e.g., '231402' for CBE)")
    account_number: str = Field(..., description="Recipient account number at destination bank")
    reference: str = Field(..., description="Unique transaction reference")
    receiver_name: str = Field(..., description="Full name of the receiver")

class BoAMoneySendRequest(BaseModel):
    """
    Request schema for money send (wallet transfer) transactions.
    """
    amount: str = Field(..., description="Transfer amount as string")
    remitter_name: str = Field(..., description="Full name of the remitter/sender")
    remitter_phone: str = Field(..., description="Remitter's phone number")
    receiver_name: str = Field(..., description="Full name of the receiver")
    receiver_address: str = Field(..., description="Receiver's address")
    receiver_phone: str = Field(..., description="Receiver's phone number")
    reference: str = Field(..., description="Unique transaction reference")
    secret_code: str = Field(..., description="Secret code for transaction verification")

# Transfer Response Schema
class BoATransferResponse(BaseModel):
    """
    Response schema for all transfer operations.
    Standard response format for within-BOA, other bank, and money send transfers.    
    """
    success: bool = Field(..., description="Whether transfer was initiated successfully")
    boa_reference: Optional[str] = Field(None, description="BOA's unique transaction reference (e.g., 'FT23343L0Z8C')")
    unique_identifier: Optional[str] = Field(None, description="Unique transaction identifier from BOA")
    transaction_status: Optional[str] = Field(None, description="Initial transaction status ('Live', 'success', 'failed')")
    response: Optional[Dict[str, Any]] = Field(None, description="Complete BOA API response for debugging")

    class Config:
        from_attributes = True

# Status Response Schema
class BoAStatusResponse(BaseModel):
    """
    Response schema for transaction status checks.
    Used to track the status of initiated transactions.
    """
    id: Optional[str] = Field(None, description="Transaction ID used in the request")
    boa_reference: Optional[str] = Field(None, description="BOA's reference number (e.g., 'FT24351516VG')")
    status: Optional[str] = Field(None, description="Current transaction status ('SUCCESS', 'FAILED', 'PENDING')")

    class Config:
        from_attributes = True

# Currency Rate Response Schema
class BoACurrencyRateResponse(BaseModel):
    """
    Response schema for currency exchange rates.

    Matches the Postman collection 'exchangeRate' response structure.
    Provides buy and sell rates for currency conversion.
    """
    currency_code: Optional[str] = Field(None, description="Currency code (e.g., 'USD')")
    currency_name: Optional[str] = Field(None, description="Full currency name (e.g., 'US Dollar')")
    buy_rate: Optional[Decimal] = Field(None, description="Rate at which BOA buys the currency")
    sell_rate: Optional[Decimal] = Field(None, description="Rate at which BOA sells the currency")

    class Config:
        from_attributes = True

# Balance Response Schema
class BoABalanceResponse(BaseModel):
    """
    Response schema for account balance inquiries.

    Matches the Postman collection 'getBalance' response structure.
    Shows the available balance on the settlement account.
    """
    account_currency: Optional[str] = Field(None, description="Account currency (typically 'ETB')")
    balance: Optional[Decimal] = Field(None, description="Current available balance on settlement account")

    class Config:
        from_attributes = True

# Bank List Response Schema
class BoABankListResponse(BaseModel):
    """
    Response schema for individual bank entries in the bank list.

    Matches the Postman collection 'bankId' response structure.
    Each bank has a unique ID used for other bank transfers.
    """
    bank_id: str = Field(..., description="Unique bank identifier (e.g., '231402' for Commercial Bank of Ethiopia)")
    institution_name: str = Field(..., description="Full name of the banking institution")

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