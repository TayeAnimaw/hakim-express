# app/routers/boa_integration.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging

from app.database.database import get_db
from app.utils.boa_service import (
    BoABeneficiaryService,
    BoATransferService,
    BoAStatusService,
    BoARateService,
    BoABankService,
    BoAServiceError
)
from app.schemas.boa_integration import (
    BoABeneficiaryResponse,
    BoATransferRequest,
    BoATransferResponse,
    BoAOtherBankTransferRequest,
    BoAStatusResponse,
    BoACurrencyRateResponse,
    BoABalanceResponse,
    BoABankListResponse,
    BoAMoneySendRequest
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Beneficiary Name Endpoints

@router.get("/beneficiary/boa/{account_id}", response_model=BoABeneficiaryResponse)
async def get_beneficiary_name_boa(
    account_id: str,
    db: Session = Depends(get_db)
):
    """
    Fetch beneficiary name for Bank of Abyssinia account
    """
    try:
        result = await BoABeneficiaryService.fetch_beneficiary_name(account_id, db)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Beneficiary not found or API error"
            )
        return BoABeneficiaryResponse(**result)
    except BoAServiceError as e:
        logger.error(f"Service error fetching BoA beneficiary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/beneficiary/other-bank/{bank_id}/{account_id}", response_model=BoABeneficiaryResponse)
async def get_beneficiary_name_other_bank(
    bank_id: str,
    account_id: str,
    db: Session = Depends(get_db)
):
    """
    Fetch beneficiary name for other bank account
    """
    try:
        result = await BoABeneficiaryService.fetch_beneficiary_name_other_bank(bank_id, account_id, db)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Beneficiary not found or API error"
            )
        return BoABeneficiaryResponse(**result)
    except BoAServiceError as e:
        logger.error(f"Service error fetching other bank beneficiary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Transfer Endpoints

@router.post("/transfer/within-boa", response_model=BoATransferResponse)
async def initiate_within_boa_transfer(
    request: BoATransferRequest,
    db: Session = Depends(get_db)
):
    """
    Initiate transfer within Bank of Abyssinia
    """
    try:
        result = await BoATransferService.initiate_within_boa_transfer(
            transaction_id=request.transaction_id,
            amount=request.amount,
            account_number=request.account_number,
            reference=request.reference,
            db=db
        )
        return BoATransferResponse(**result)
    except BoAServiceError as e:
        logger.error(f"Service error initiating BoA transfer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/transfer/other-bank", response_model=BoATransferResponse)
async def initiate_other_bank_transfer(
    request: BoAOtherBankTransferRequest,
    db: Session = Depends(get_db)
):
    """
    Initiate transfer to other bank using EthSwitch
    """
    try:
        result = await BoATransferService.initiate_other_bank_transfer(
            transaction_id=request.transaction_id,
            amount=request.amount,
            bank_code=request.bank_code,
            account_number=request.account_number,
            reference=request.reference,
            receiver_name=request.receiver_name,
            db=db
        )
        return BoATransferResponse(**result)
    except BoAServiceError as e:
        logger.error(f"Service error initiating other bank transfer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/transfer/money-send", response_model=BoATransferResponse)
async def initiate_money_send(
    request: BoAMoneySendRequest,
    db: Session = Depends(get_db)
):
    """
    Initiate money send (wallet transfer)
    """
    try:
        # Import here to avoid circular imports
        from app.utils.boa_api_service import boa_api

        result = await boa_api.initiate_money_send(
            amount=request.amount,
            remitter_name=request.remitter_name,
            remitter_phone=request.remitter_phone,
            receiver_name=request.receiver_name,
            receiver_address=request.receiver_address,
            receiver_phone=request.receiver_phone,
            reference=request.reference,
            secret_code=request.secret_code
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Empty response from BoA API"
            )

        header = result.get("header", {})
        if header.get("status") != "success":
            error_msg = "Money send failed"
            if "error" in result:
                error_msg = result["error"].get("errorDetails", [{}])[0].get("message", error_msg)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )

        return BoATransferResponse(
            success=True,
            boa_reference=header.get("id"),
            unique_identifier=header.get("uniqueIdentifier"),
            transaction_status=header.get("transactionStatus"),
            response=result
        )

    except BoAServiceError as e:
        logger.error(f"Service error initiating money send: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Status and Inquiry Endpoints

@router.get("/transaction-status/{transaction_id}", response_model=BoAStatusResponse)
async def check_transaction_status(
    transaction_id: str,
    db: Session = Depends(get_db)
):
    """
    Check status of a BoA transaction
    """
    try:
        result = await BoAStatusService.check_transaction_status(transaction_id, db)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found or API error"
            )
        return BoAStatusResponse(**result)
    except BoAServiceError as e:
        logger.error(f"Service error checking transaction status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/currency-rate/{base_currency}", response_model=BoACurrencyRateResponse)
async def get_currency_rate(
    base_currency: str,
    db: Session = Depends(get_db)
):
    """
    Get currency exchange rate from BoA
    """
    try:
        result = await BoARateService.get_currency_rate(base_currency.upper(), db)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Currency rate not found or API error"
            )
        return BoACurrencyRateResponse(**result)
    except BoAServiceError as e:
        logger.error(f"Service error getting currency rate: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/balance", response_model=BoABalanceResponse)
async def get_balance(
    db: Session = Depends(get_db)
):
    """
    Get BoA account balance
    """
    try:
        result = await BoARateService.get_balance(db)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Balance not found or API error"
            )
        return BoABalanceResponse(**result)
    except BoAServiceError as e:
        logger.error(f"Service error getting balance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/banks", response_model=List[BoABankListResponse])
async def get_bank_list(
    db: Session = Depends(get_db)
):
    """
    Get list of available banks for other bank transfers
    """
    try:
        result = await BoABankService.get_bank_list(db)
        return [BoABankListResponse(**bank) for bank in result]
    except BoAServiceError as e:
        logger.error(f"Service error getting bank list: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Utility Endpoints

@router.post("/refresh-bank-list")
async def refresh_bank_list(
    db: Session = Depends(get_db)
):
    """
    Refresh the bank list from BoA API (admin function)
    """
    try:
        result = await BoABankService.get_bank_list(db)
        return {
            "message": "Bank list refreshed successfully",
            "banks_count": len(result),
            "banks": result
        }
    except BoAServiceError as e:
        logger.error(f"Service error refreshing bank list: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/test-connection")
async def test_boa_connection():
    """
    Test connection to Bank of Abyssinia API
    """
    try:
        # Import here to avoid circular imports
        from app.utils.boa_api_service import boa_api

        # Try to get access token (this will test authentication)
        await boa_api._ensure_authenticated()

        return {
            "status": "success",
            "message": "Successfully connected to Bank of Abyssinia API",
            "base_url": boa_api.base_url
        }
    except Exception as e:
        logger.error(f"Connection test failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Connection test failed: {str(e)}"
        )