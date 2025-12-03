# app/routers/boa_integration.py

import json
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
from app.utils.boa_api_service import boa_api

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

@router.get("/beneficiary/boa/{account_id}", response_model=BoABeneficiaryResponse, summary="Fetch BOA Beneficiary Name", description="Fetches the beneficiary name for a Bank of Abyssinia account number. Uses caching for 24 hours to improve performance.")
async def get_beneficiary_name_boa(
    account_id: str,
    db: Session = Depends(get_db)
):
    try:
        # change the implementation to boa_api service direct call
        result =await boa_api.fetch_beneficiary_name(account_id)
        result_body_list = result.get("body", [])
        status_code = result.get("http_status", 200)
        if(status_code != 200):
            try: 
                error_message = result.get("error",{}).get("message", "Try again later")
            except:
                error_message = "Try again later"
            return JSONResponse(
                status_code=status_code,
                content={
                    "success": False,
                    "message" : error_message
                }
            )
        if not result_body_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Beneficiary not found or API error"
            )

        # BoA returns a list with one object, so take the first item
        boa_data = result_body_list[0]

        mapped_data = {
            "customer_name": boa_data.get("customerName"),
            "account_currency": boa_data.get("accountCurrency"),
            "enquiry_status": None,   # BoA does not return this field
            "cached": False
        }

        return BoABeneficiaryResponse(**mapped_data)
    except BoAServiceError as e:
        logger.error(f"Service error fetching BoA beneficiary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/beneficiary/other-bank/{bank_id}/{account_id}", response_model=BoABeneficiaryResponse, summary="Fetch Other Bank Beneficiary Name", description="Fetches the beneficiary name for an account in another Ethiopian bank using EthSwitch.")
async def get_beneficiary_name_other_bank(
    bank_id: str,
    account_id: str,
    db: Session = Depends(get_db)
):
    """
    Fetch beneficiary name for other bank account.

    This endpoint queries the Bank of Abyssinia API to retrieve the account holder's name
    for the specified account number in another Ethiopian bank.

    **Parameters:**
    - `bank_id`: The destination bank ID (e.g., "231402" for Commercial Bank of Ethiopia)
    - `account_id`: The account number at the destination bank

    **Returns:**
    - `customer_name`: Account holder's full name
    - `account_currency`: Account currency
    - `enquiry_status`: "1" for success, "0" for failure
    - `cached`: Boolean indicating if result came from cache

    **Postman Collection Reference:**
    - Folder: "otherBank transfer"
    - Request: "accountQuery"
    - URL: `{{base_url}}/otherBank/getAccount/${bankId}/${accountId}`
    - Headers: `x-api-key`, `Authorization`
    """
    try:
        # change the implementation to boa_api service direct call
        result = await boa_api.fetch_beneficiary_name_other_bank(bank_id, account_id)
        print("==========================")
        print(result)
        print("111111111111111111111")
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

@router.post(
    "/transfer/within-boa",
    response_model=BoATransferResponse,
    summary="Initiate Within-BOA Transfer",
    description="Initiates a real-time transfer between accounts within Bank of Abyssinia."
)
async def initiate_within_boa_transfer(
    request: BoATransferRequest,
    db: Session = Depends(get_db)
):
    try:
        result = await boa_api.initiate_within_boa_transfer(
            amount=request.amount,
            account_number=request.account_number,
            reference=request.reference
        )

        header = result.get("header", {})
        body = result.get("body", {})

        # BoA Code (not HTTP!)
        boa_status_code = result.get("http_status", 200)

        # If like 401, 404, 100, 500, return EXACT status
        print(result)
        if boa_status_code != 200:
            try:
                error_data = result.get("error", {}).get("errorDetails", [])
                error_message = "Transaction Failed" if error_data == [] else error_data[0].get("message", "Transaction Failed")
            except:
                error_message = "Transaction Failed"
            
            return JSONResponse(
                status_code=boa_status_code,
                content={
                    "success": False,
                    "boa_reference": header.get("id"),
                    "unique_identifier": header.get("uniqueIdentifier"),
                    "transaction_status": header.get("transactionStatus"),
                    "message": error_message
                }
            )

        # SUCCESS mapping
        mapped_response = {
            "success": header.get("status") == "success",
            "boa_reference": header.get("id"),
            "unique_identifier": header.get("uniqueIdentifier"),
            "transaction_status": header.get("transactionStatus"),
            "response": body
        }

        return BoATransferResponse(**mapped_response)

    except Exception as e:
        logger.error(f"Unexpected error during BOA transfer: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "error": str(e)}
        )
@router.post(
    "/transfer/other-bank",
    response_model=BoATransferResponse,
    summary="Initiate Other Bank Transfer",
    description="Initiates a transfer to an account in another Ethiopian bank using EthSwitch."
)
async def initiate_other_bank_transfer(
    request: BoAOtherBankTransferRequest,
    db: Session = Depends(get_db)
):
    try:
        result = await boa_api.initiate_other_bank_transfer(
            amount=request.amount,
            bank_code=request.bank_code,
            account_number=request.account_number,
            reference=request.reference,
            receiver_name=request.receiver_name
        )

        header = result.get("header", {})
        body = result.get("body", result)
        boa_status_code = result.get("http_status", 200)
        if boa_status_code != 200:
            try:
                error_data = result.get("error", {}).get("errorDetails", [])
                error_message = (
                    "Transaction Failed"
                    if not error_data
                    else error_data[0].get("message", "Transaction Failed")
                )
            except:
                error_message = "Transaction Failed"

            return JSONResponse(
                status_code=boa_status_code,
                content={
                    "success": False,
                    "boa_reference": header.get("id"),
                    "unique_identifier": header.get("uniqueIdentifier"),
                    "transaction_status": header.get("transactionStatus"),
                    "message": error_message,
                   
                }
            )

        mapped_response = {
            "success": header.get("status") == "success",
            "boa_reference": header.get("id"),
            "unique_identifier": header.get("uniqueIdentifier"),
            "transaction_status": header.get("transactionStatus"),
            "response": body
        }

        return BoATransferResponse(**mapped_response)

    except Exception as e:
        logger.error(f"Unexpected error during BOA other bank transfer: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "error": str(e)}
        )

@router.post("/transfer/money-send", response_model=BoATransferResponse, summary="Initiate Money Send", description="Initiates a money send transaction (wallet transfer) through BOA.")
async def initiate_money_send(
    request: BoAMoneySendRequest,
    db: Session = Depends(get_db)
):
    """
    Initiate money send (wallet transfer).

    This endpoint performs money send transactions, typically for mobile wallet transfers.
    Requires remitter and receiver details along with transaction information.

    **Request Body:**
    - `amount`: Transfer amount as string
    - `remitter_name`: Full name of the sender
    - `remitter_phone`: Sender's phone number
    - `receiver_name`: Full name of the recipient
    - `receiver_address`: Recipient's address
    - `receiver_phone`: Recipient's phone number
    - `reference`: Unique transaction reference
    - `secret_code`: Secret code for transaction verification

    **Returns:**
    - `success`: Boolean indicating if transfer was initiated successfully
    - `boa_reference`: BOA's unique transaction reference
    - `unique_identifier`: Unique transaction identifier
    - `transaction_status`: Current status

    **Note:** This endpoint calls the BOA API directly without database persistence.
    """
    try:
        # Import here to avoid circular imports
        
         
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
        print(result)
        header = result.get("header", {})
        body = result.get("body", [])
        status_code = result.get("http_status", 200)
        if (status_code != 200):
            try:
                error_data = result.get("error", {}).get("errorDetails", [])
                error_message = (
                    "Transaction Failed"
                    if not error_data
                    else error_data[0].get("message", "Transaction Failed")
                )
            except:
                error_message = "Transaction Failed"
            return JSONResponse(
                status_code = status_code,
                content = {
                    "success" : False,
                    "message" : error_message
                }
            )
        if not result or not body:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Empty response from BoA API"
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

@router.get("/transaction-status/{transaction_id}", response_model=BoAStatusResponse, summary="Check Transaction Status", description="Queries the current status of a previously initiated BOA transaction.")
async def check_transaction_status(
    transaction_id: str,
    db: Session = Depends(get_db)
):
    """
    Check status of a BoA transaction.

    This endpoint allows real-time tracking of transaction status after initiation.
    Useful for monitoring pending, successful, or failed transactions.

    **Parameters:**
    - `transaction_id`: The unique reference used during transaction initiation

    **Returns:**
    - `id`: Transaction ID
    - `boa_reference`: BOA's reference number (e.g., "FT24351516VG")
    - `status`: Current status ("SUCCESS", "FAILED", "PENDING", etc.)

    **Postman Collection Reference:**
    - Request: "statuCheck"
    - URL: `{{base_url}}/transactionStatus/{transactionId}`
    - Headers: `x-api-key`, `Authorization`
    """
    try:
        # change the implimentation to boa_api service direct call
        result = await boa_api.check_transaction_status(transaction_id)
        # result = await BoAStatusService.check_transaction_status(transaction_id, db)
        print(result)
        header = result.get("header", {})
        body = result.get("body", {})
        status_code = result.get("http_status", 200)
        if(status_code != 200):
            try:
                error_message = result.get("error",{}).get("message", "Try again later")
            except:
                error_message = "Try again later"
            return JSONResponse(
                status_code = status_code,
                content = {
                    "success" : False,
                    "message" : error_message
                }
            )
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

@router.get("/currency-rate/{base_currency}", response_model=BoACurrencyRateResponse, summary="Get Currency Exchange Rate", description="Retrieves real-time currency exchange rates from Bank of Abyssinia.")
async def get_currency_rate(
    base_currency: str,
    db: Session = Depends(get_db)
):
    try:
        # change the implementation to boa_api service direct call
        result = await boa_api.get_currency_rate(base_currency.upper())
        body = result.get("body",[])
        status_code = result.get("http_status", 200)
        if(status_code != 200):
            try:
                error_message = result.get("error",{}).get("message", "Try again later")
            except:
                error_message = "Try again later"
            return JSONResponse(
                status_code=status_code,
                content={
                    "success": False,
                    "message": error_message,                  
                }
            )
        if not result or not body:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Currency rate not found or API error"
            )
        currency_data = body[0]
        result_modified = {
            "currency_code" : currency_data.get("currencyCode", "Unknown"),
            "currency_name" : currency_data.get("currencyName", "Unknown"),
            "buy_rate" : currency_data.get("buyRate", 0.00),
            "sell_rate" : currency_data.get("sellRate", 0.00)
        }
        return BoACurrencyRateResponse(**result_modified)
    except BoAServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/balance", response_model=BoABalanceResponse, summary="Get Account Balance", description="Retrieves the current balance of the remitter's settlement account at Bank of Abyssinia.")
async def get_balance(
    db: Session = Depends(get_db)
):

    try:
        # change the implementation to boa_api service direct call
        result = await boa_api.get_balance()
        header = result.get("header", {})
        body = result.get("body", [])
        status_code = result.get("http_status", 200)
        if (status_code != 200):
            try:
                error_message = result.get("error", {}).get("message", "Try again later")
            except:
                error_message = "Try again later"
            return JSONResponse(
                status_code=status_code,
                content={
                    "success" : False,
                    "message" : error_message
                }
            )
        
        if not result or not body:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Balance not found or API error"
            )
        balance_data = body[0]
        result_modified = {
            "account_currency" : balance_data.get("accountCurrency", "ETB"),
            "balance" : balance_data.get("workingBalance", 0.00)
        }
        return BoABalanceResponse(**result_modified)
    except BoAServiceError as e:
        # logger.error(f"Service error getting balance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/banks", response_model=List[BoABankListResponse], summary="Get Bank List", description="Retrieves the complete list of Ethiopian banks supported for inter-bank transfers via EthSwitch.")
async def get_bank_list(
    db: Session = Depends(get_db)
):
    
    try:
        result = await boa_api.get_bank_list()

        boa_banks = result.get("body", [])
        status_code = result.get("http_status", 200)
        if (status_code != 200):
            try:
                error_message = result.get("error", {}).get("message", "Try again later")
            except:
                error_message = "Try again later"
            return JSONResponse(
                status_code=status_code,
                content={
                    "success" : False,
                    "message" : error_message
                }
            )
        modified_list = [
            {
                "bank_id": bank["id"],
                "institution_name": bank["institutionName"]
            }
            for bank in boa_banks
        ]

        # Return Pydantic validated list
        return [BoABankListResponse(**bank) for bank in modified_list]
    except BoAServiceError as e:
        logger.error(f"Service error getting bank list: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Utility Endpoints

@router.post("/refresh-bank-list", summary="Refresh Bank List", description="Manually refreshes the bank list from BOA API and updates the local database. Admin function.")
async def refresh_bank_list(
    db: Session = Depends(get_db)
):

    try:
        # change the implementation to boa_api service direct call
        result = await boa_api.get_bank_list()
        # result = await BoABankService.get_bank_list(db)
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

@router.get("/test-connection", summary="Test BOA Connection", description="Tests the connection to Bank of Abyssinia API by attempting authentication.")
async def test_boa_connection():

    try:
        # Import here to avoid circular imports
        # from app.utils.boa_api_service import boa_api

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