# app/routers/boa_integration.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
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
    """
    Fetch beneficiary name for Bank of Abyssinia account.

    This endpoint queries the Bank of Abyssinia API to retrieve the account holder's name
    for the specified account number. Results are cached for 24 hours.

    **Parameters:**
    - `account_id`: The BOA account number to query

    **Returns:**
    - `customer_name`: Account holder's full name
    - `account_currency`: Account currency (e.g., "ETB")
    - `cached`: Boolean indicating if result came from cache

    **Postman Collection Reference:**
    - Folder: "with-in-boa"
    - Request: "accountQuery"
    - URL: `{{base_url}}/getAccount/${accountId}`
    - Headers: `x-api-key`, `Authorization`
    """
    try:
        # change the implimentation to boa_api service direct call
        result =await boa_api.fetch_beneficiary_name(account_id)
        print(result)
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
        # change the implimentation to boa_api service direct call
        result = await boa_api.fetch_beneficiary_name_other_bank(bank_id, account_id)
        print(result)
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

@router.post("/transfer/within-boa", response_model=BoATransferResponse, summary="Initiate Within-BOA Transfer", description="Initiates a real-time transfer between accounts within Bank of Abyssinia.")
async def initiate_within_boa_transfer(
    request: BoATransferRequest,
    db: Session = Depends(get_db)
):
    """
    Initiate transfer within Bank of Abyssinia.

    This endpoint performs real-time transfers between accounts held at Bank of Abyssinia.
    The transfer is processed immediately and returns transaction details.

    **Request Body:**
    - `transaction_id`: Internal transaction reference ID
    - `amount`: Transfer amount as string
    - `account_number`: Recipient's BOA account number
    - `reference`: Unique transaction reference

    **Returns:**
    - `success`: Boolean indicating if transfer was initiated successfully
    - `boa_reference`: BOA's unique transaction reference (e.g., "FT23343L0Z8C")
    - `unique_identifier`: Unique transaction identifier
    - `transaction_status`: Current status ("Live", "success", "failed")

    **Postman Collection Reference:**
    - Folder: "with-in-boa"
    - Request: "transfer"
    - URL: `{{base_url}}/transferWithin`
    - Headers: `x-api-key`, `Authorization`
    - Body: `{"client_id": "{{client_id}}", "amount": "100", "accountNumber": "7260865", "reference": "stringETSW"}`
    """
    try:
        # change the implimentation to boa_api service direct call
        result = await boa_api.initiate_within_boa_transfer(
            amount=request.amount,
            account_number=request.account_number,
            reference=request.reference
        )
        # result = await BoATransferService.initiate_within_boa_transfer(
        #     transaction_id=request.transaction_id,
        #     amount=request.amount,
        #     account_number=request.account_number,
        #     reference=request.reference,
        #     db=db
        # )
        print(result)
        return BoATransferResponse(**result)
    except BoAServiceError as e:
        logger.error(f"Service error initiating BoA transfer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/transfer/other-bank", response_model=BoATransferResponse, summary="Initiate Other Bank Transfer", description="Initiates a transfer to an account in another Ethiopian bank using EthSwitch.")
async def initiate_other_bank_transfer(
    request: BoAOtherBankTransferRequest,
    db: Session = Depends(get_db)
):
    """
    Initiate transfer to other bank using EthSwitch.

    This endpoint performs transfers to accounts in other Ethiopian banks through the
    EthSwitch network. Requires the destination bank ID and account details.

    **Request Body:**
    - `transaction_id`: Internal transaction reference ID
    - `amount`: Transfer amount as string
    - `bank_code`: Destination bank ID (e.g., "231402" for Commercial Bank of Ethiopia)
    - `account_number`: Recipient's account number at destination bank
    - `reference`: Unique transaction reference
    - `receiver_name`: Full name of the recipient

    **Returns:**
    - `success`: Boolean indicating if transfer was initiated successfully
    - `boa_reference`: BOA's unique transaction reference
    - `unique_identifier`: Unique transaction identifier
    - `transaction_status`: Current status

    **Postman Collection Reference:**
    - Folder: "otherBank transfer"
    - Request: "otherBank EthSwitch"
    - URL: `{{base_url}}/otherBank/transferEthswitch`
    - Headers: `x-api-key`, `Authorization`
    - Body: `{"client_id": "{{client_id}}", "amount": "{{amount}}", "bankCode": "{{bank_id}}", "receiverName": "{{other_bank_receiverName}}", "accountNumber": "{{other_bank_account_number}}", "reference": "{{otherbank_transfer_reference}}"}`
    """
    try:
        # change the implimentation to boa_api service direct call
        result = await boa_api.initiate_other_bank_transfer(
            amount=request.amount,
            bank_code=request.bank_code,
            account_number=request.account_number,
            reference=request.reference,
            receiver_name=request.receiver_name
        )
        print(result)
        # result = await BoATransferService.initiate_other_bank_transfer(
        #     transaction_id=request.transaction_id,
        #     amount=request.amount,
        #     bank_code=request.bank_code,
        #     account_number=request.account_number,
        #     reference=request.reference,
        #     receiver_name=request.receiver_name,
        #     db=db
        # )
        return BoATransferResponse(**result)
    except BoAServiceError as e:
        logger.error(f"Service error initiating other bank transfer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
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
    """
    Get currency exchange rate from BoA.

    This endpoint fetches up-to-date currency exchange rates for remittance calculations.
    Rates are cached in the database for performance.

    **Parameters:**
    - `base_currency`: Base currency code (e.g., "USD", "EUR", "GBP")

    **Returns:**
    - `currency_code`: Currency code
    - `currency_name`: Full currency name
    - `buy_rate`: Rate at which BOA buys the currency
    - `sell_rate`: Rate at which BOA sells the currency

    **Postman Collection Reference:**
    - Request: "exchangeRate"
    - URL: `{{base_url}}/rate/${baseCurrency}`
    - Headers: `x-api-key`, `Authorization`
    - Example: `{{base_url}}/rate/USD`
    """
    try:
        # change the implimentation to boa_api service direct call
        result = await boa_api.get_currency_rate(base_currency.upper())
        # result = await BoARateService.get_currency_rate(base_currency.upper(), db)
        print(result)
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

@router.get("/balance", response_model=BoABalanceResponse, summary="Get Account Balance", description="Retrieves the current balance of the remitter's settlement account at Bank of Abyssinia.")
async def get_balance(
    db: Session = Depends(get_db)
):
    """
    Get BoA account balance.

    This endpoint returns the available balance on the settlement account that is debited
    for every transfer request. Essential for checking available funds before transactions.

    **Returns:**
    - `account_currency`: Account currency (typically "ETB")
    - `balance`: Current available balance

    **Postman Collection Reference:**
    - Request: "getBalance"
    - URL: `{{base_url}}/getBalance`
    - Method: POST
    - Headers: `x-api-key`, `Authorization`
    - Body: `{"client_id": "{{client_id}}"}`
    """
    try:
        # change the implimentation to boa_api service direct call
        result = await boa_api.get_balance()
        # result = await BoARateService.get_balance(db)
        print(result)
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

@router.get("/banks", response_model=List[BoABankListResponse], summary="Get Bank List", description="Retrieves the complete list of Ethiopian banks supported for inter-bank transfers via EthSwitch.")
async def get_bank_list(
    db: Session = Depends(get_db)
):
    """
    Get list of available banks for other bank transfers.

    This endpoint provides all Ethiopian banks that can receive transfers through EthSwitch.
    The list includes bank codes and names required for other bank transfer requests.

    **Returns:**
    - Array of banks with `bank_id` and `institution_name`
    - Example: `[{"bank_id": "231402", "institution_name": "Commercial Bank of Ethiopia"}]`

    **Postman Collection Reference:**
    - Folder: "otherBank transfer"
    - Request: "bankId"
    - URL: `{{base_url}}/otherBank/bankId`
    - Headers: `x-api-key`, `Authorization`
    """
    try:
        result = await boa_api.get_bank_list()

        boa_banks = result.get("body", [])
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
    """
    Refresh the bank list from BoA API (admin function).

    This endpoint fetches the latest bank list from Bank of Abyssinia and updates
    the local database. Useful for ensuring the bank directory is current.

    **Returns:**
    - `message`: Success message
    - `banks_count`: Number of banks updated
    - `banks`: Array of all banks with their details
    """
    try:
        # change the implimentation to boa_api service direct call
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
    """
    Test connection to Bank of Abyssinia API.

    This endpoint attempts to authenticate with the BOA API to verify connectivity.
    Useful for checking if VPN connection and API credentials are working correctly.

    **Returns:**
    - `status`: "success" if connection works
    - `message`: Descriptive message
    - `base_url`: The configured BOA API base URL

    **Note:** This endpoint only tests authentication, not actual API calls.
    """
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