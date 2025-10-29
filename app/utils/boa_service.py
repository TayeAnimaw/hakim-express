# app/utils/boa_service.py

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
import logging
from typing import Optional, Dict, Any, List

from .boa_api_service import boa_api, BoAAuthenticationError, BoAAPIError, BoARateLimitError
from app.models.boa_integration import (
    BoATransaction, BoABeneficiaryInquiry, BoABankList,
    BoACurrencyRate, BoABalance
)
from app.database.database import SessionLocal

logger = logging.getLogger(__name__)

class BoAServiceError(Exception):
    """Base exception for BoA service errors"""
    pass

class BoABeneficiaryService:
    """Service for handling beneficiary-related operations"""

    @staticmethod
    async def fetch_beneficiary_name(account_id: str, db: Session) -> Optional[Dict[str, Any]]:
        """
        Fetch beneficiary name for BoA account
        Returns cached result if available and not expired
        """
        try:
            # Check cache first (24 hours expiry)
            cached = db.query(BoABeneficiaryInquiry).filter(
                BoABeneficiaryInquiry.account_id == account_id,
                BoABeneficiaryInquiry.inquiry_type == "boa",
                BoABeneficiaryInquiry.expires_at > datetime.utcnow()
            ).first()

            if cached:
                logger.info(f"Returning cached beneficiary info for account {account_id}")
                return {
                    "customer_name": cached.customer_name,
                    "account_currency": cached.account_currency,
                    "cached": True
                }

            # Fetch from BoA API
            response = await boa_api.fetch_beneficiary_name(account_id)

            if not response or response.get("header", {}).get("status") != "success":
                logger.error(f"Failed to fetch beneficiary name for account {account_id}")
                return None

            body = response.get("body", [])
            if not body or len(body) == 0:
                logger.error(f"No beneficiary data found for account {account_id}")
                return None

            beneficiary_data = body[0]
            customer_name = beneficiary_data.get("customerName")
            account_currency = beneficiary_data.get("accountCurrency")

            # Cache the result
            inquiry = BoABeneficiaryInquiry(
                account_id=account_id,
                inquiry_type="boa",
                customer_name=customer_name,
                account_currency=account_currency,
                enquiry_status="1",  # Success
                boa_response=response,
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            db.add(inquiry)
            db.commit()

            logger.info(f"Successfully fetched and cached beneficiary info for account {account_id}")
            return {
                "customer_name": customer_name,
                "account_currency": account_currency,
                "cached": False
            }

        except (BoAAuthenticationError, BoAAPIError, BoARateLimitError) as e:
            logger.error(f"BoA API error fetching beneficiary name: {str(e)}")
            raise BoAServiceError(f"Failed to fetch beneficiary name: {str(e)}")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error caching beneficiary info: {str(e)}")
            raise BoAServiceError(f"Database error: {str(e)}")

    @staticmethod
    async def fetch_beneficiary_name_other_bank(bank_id: str, account_id: str, db: Session) -> Optional[Dict[str, Any]]:
        """
        Fetch beneficiary name for other bank account
        """
        try:
            # Check cache first
            cache_key = f"{bank_id}_{account_id}"
            cached = db.query(BoABeneficiaryInquiry).filter(
                BoABeneficiaryInquiry.account_id == account_id,
                BoABeneficiaryInquiry.bank_id == bank_id,
                BoABeneficiaryInquiry.inquiry_type == "other_bank",
                BoABeneficiaryInquiry.expires_at > datetime.utcnow()
            ).first()

            if cached:
                logger.info(f"Returning cached other bank beneficiary info for {cache_key}")
                return {
                    "customer_name": cached.customer_name,
                    "account_currency": cached.account_currency,
                    "enquiry_status": cached.enquiry_status,
                    "cached": True
                }

            # Fetch from BoA API
            response = await boa_api.fetch_beneficiary_name_other_bank(bank_id, account_id)

            if not response:
                logger.error(f"Empty response from BoA API for other bank inquiry {cache_key}")
                return None

            header = response.get("header", {})
            body = response.get("body", {})

            if header.get("status") != "success":
                logger.error(f"BoA API returned error for other bank inquiry {cache_key}: {header}")
                return None

            customer_name = body.get("customerName")
            account_currency = body.get("accountCurrency")
            enquiry_status = body.get("enquiryStatus")

            # Cache the result
            inquiry = BoABeneficiaryInquiry(
                account_id=account_id,
                bank_id=bank_id,
                inquiry_type="other_bank",
                customer_name=customer_name,
                account_currency=account_currency,
                enquiry_status=enquiry_status,
                boa_response=response,
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            db.add(inquiry)
            db.commit()

            logger.info(f"Successfully fetched and cached other bank beneficiary info for {cache_key}")
            return {
                "customer_name": customer_name,
                "account_currency": account_currency,
                "enquiry_status": enquiry_status,
                "cached": False
            }

        except (BoAAuthenticationError, BoAAPIError, BoARateLimitError) as e:
            logger.error(f"BoA API error fetching other bank beneficiary name: {str(e)}")
            raise BoAServiceError(f"Failed to fetch other bank beneficiary name: {str(e)}")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error caching other bank beneficiary info: {str(e)}")
            raise BoAServiceError(f"Database error: {str(e)}")


class BoATransferService:
    """Service for handling transfer operations"""

    @staticmethod
    async def initiate_within_boa_transfer(
        transaction_id: int,
        amount: str,
        account_number: str,
        reference: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Initiate transfer within Bank of Abyssinia
        """
        try:
            # Call BoA API
            response = await boa_api.initiate_within_boa_transfer(
                amount=amount,
                account_number=account_number,
                reference=reference
            )

            if not response:
                raise BoAServiceError("Empty response from BoA API")

            header = response.get("header", {})
            body = response.get("body", {})

            if header.get("status") != "success":
                error_msg = "Transfer failed"
                if "error" in response:
                    error_msg = response["error"].get("errorDetails", [{}])[0].get("message", error_msg)
                raise BoAServiceError(f"BoA transfer failed: {error_msg}")

            # Save transaction details
            boa_transaction = BoATransaction(
                transaction_id=transaction_id,
                boa_reference=header.get("id"),
                unique_identifier=header.get("uniqueIdentifier"),
                transaction_type=body.get("transactionType"),
                boa_transaction_status=header.get("transactionStatus"),
                debit_account_id=body.get("debitAccountId"),
                credit_account_id=body.get("creditAccountId"),
                debit_amount=body.get("debitAmount"),
                credit_amount=body.get("creditAmount"),
                debit_currency=body.get("debitCurrency"),
                credit_currency=body.get("creditCurrency"),
                reason=body.get("reason"),
                transaction_date=body.get("transactionDate"),
                infinity_reference=body.get("infinityReference"),
                audit_info=header.get("audit"),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(boa_transaction)
            db.commit()

            logger.info(f"Successfully initiated BoA transfer for transaction {transaction_id}")
            return {
                "success": True,
                "boa_reference": header.get("id"),
                "unique_identifier": header.get("uniqueIdentifier"),
                "transaction_status": header.get("transactionStatus"),
                "response": response
            }

        except (BoAAuthenticationError, BoAAPIError, BoARateLimitError) as e:
            logger.error(f"BoA API error during transfer: {str(e)}")
            raise BoAServiceError(f"Transfer failed: {str(e)}")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error saving BoA transaction: {str(e)}")
            raise BoAServiceError(f"Database error: {str(e)}")

    @staticmethod
    async def initiate_other_bank_transfer(
        transaction_id: int,
        amount: str,
        bank_code: str,
        account_number: str,
        reference: str,
        receiver_name: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Initiate transfer to other bank using EthSwitch
        """
        try:
            # Call BoA API
            response = await boa_api.initiate_other_bank_transfer(
                amount=amount,
                bank_code=bank_code,
                account_number=account_number,
                reference=reference,
                receiver_name=receiver_name
            )

            if not response:
                raise BoAServiceError("Empty response from BoA API")

            header = response.get("header", {})
            body = response.get("body", {})

            if header.get("status") != "success":
                error_msg = "Other bank transfer failed"
                if "error" in response:
                    error_msg = response["error"].get("errorDetails", [{}])[0].get("message", error_msg)
                raise BoAServiceError(f"BoA other bank transfer failed: {error_msg}")

            # Save transaction details
            boa_transaction = BoATransaction(
                transaction_id=transaction_id,
                boa_reference=header.get("id"),
                unique_identifier=header.get("uniqueIdentifier"),
                transaction_type="other_bank_ethswitch",
                boa_transaction_status=header.get("transactionStatus"),
                debit_account_id=body.get("debitAccountId"),
                credit_account_id=body.get("creditAccountId"),
                debit_amount=body.get("debitAmount"),
                credit_amount=body.get("creditAmount"),
                debit_currency=body.get("debitCurrency"),
                credit_currency=body.get("creditCurrency"),
                reason=body.get("reason"),
                transaction_date=body.get("transactionDate"),
                audit_info=header.get("audit"),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(boa_transaction)
            db.commit()

            logger.info(f"Successfully initiated other bank transfer for transaction {transaction_id}")
            return {
                "success": True,
                "boa_reference": header.get("id"),
                "unique_identifier": header.get("uniqueIdentifier"),
                "transaction_status": header.get("transactionStatus"),
                "response": response
            }

        except (BoAAuthenticationError, BoAAPIError, BoARateLimitError) as e:
            logger.error(f"BoA API error during other bank transfer: {str(e)}")
            raise BoAServiceError(f"Other bank transfer failed: {str(e)}")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error saving other bank BoA transaction: {str(e)}")
            raise BoAServiceError(f"Database error: {str(e)}")


class BoAStatusService:
    """Service for checking transaction status and other inquiries"""

    @staticmethod
    async def check_transaction_status(transaction_id: str, db: Session) -> Optional[Dict[str, Any]]:
        """
        Check status of a BoA transaction
        """
        try:
            response = await boa_api.check_transaction_status(transaction_id)

            if not response:
                logger.error(f"Empty response from BoA status check for {transaction_id}")
                return None

            header = response.get("header", {})
            body = response.get("body", [])

            if header.get("status") != "success" or not body:
                logger.error(f"BoA status check failed for {transaction_id}: {header}")
                return None

            status_data = body[0]
            return {
                "id": status_data.get("id"),
                "boa_reference": status_data.get("boaReference"),
                "status": status_data.get("status")
            }

        except (BoAAuthenticationError, BoAAPIError, BoARateLimitError) as e:
            logger.error(f"BoA API error checking transaction status: {str(e)}")
            raise BoAServiceError(f"Status check failed: {str(e)}")


class BoARateService:
    """Service for currency rates and balance"""

    @staticmethod
    async def get_currency_rate(base_currency: str, db: Session) -> Optional[Dict[str, Any]]:
        """
        Get currency exchange rate from BoA
        """
        try:
            response = await boa_api.get_currency_rate(base_currency)

            if not response:
                logger.error(f"Empty response from BoA rate API for {base_currency}")
                return None

            header = response.get("header", {})
            body = response.get("body", [])

            if header.get("status") != "success" or not body:
                logger.error(f"BoA rate API failed for {base_currency}: {header}")
                return None

            rate_data = body[0]

            # Update database
            existing_rate = db.query(BoACurrencyRate).filter(
                BoACurrencyRate.currency_code == base_currency
            ).first()

            if existing_rate:
                existing_rate.buy_rate = rate_data.get("buyRate")
                existing_rate.sell_rate = rate_data.get("sellRate")
                existing_rate.currency_name = rate_data.get("currencyName")
                existing_rate.boa_response = response
                existing_rate.last_updated = datetime.utcnow()
            else:
                new_rate = BoACurrencyRate(
                    currency_code=base_currency,
                    currency_name=rate_data.get("currencyName"),
                    buy_rate=rate_data.get("buyRate"),
                    sell_rate=rate_data.get("sellRate"),
                    boa_response=response,
                    last_updated=datetime.utcnow()
                )
                db.add(new_rate)

            db.commit()

            return {
                "currency_code": rate_data.get("currencyCode"),
                "currency_name": rate_data.get("currencyName"),
                "buy_rate": rate_data.get("buyRate"),
                "sell_rate": rate_data.get("sellRate")
            }

        except (BoAAuthenticationError, BoAAPIError, BoARateLimitError) as e:
            logger.error(f"BoA API error getting currency rate: {str(e)}")
            raise BoAServiceError(f"Currency rate fetch failed: {str(e)}")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error saving currency rate: {str(e)}")
            raise BoAServiceError(f"Database error: {str(e)}")

    @staticmethod
    async def get_balance(db: Session) -> Optional[Dict[str, Any]]:
        """
        Get BoA account balance
        """
        try:
            response = await boa_api.get_balance()

            if not response:
                logger.error("Empty response from BoA balance API")
                return None

            header = response.get("header", {})
            body = response.get("body", {})

            if header.get("status") != "success":
                logger.error(f"BoA balance API failed: {header}")
                return None

            # Update database
            balance_entry = BoABalance(
                account_currency=body.get("accountCurrency"),
                balance=body.get("balance"),
                boa_response=response,
                last_updated=datetime.utcnow()
            )
            db.add(balance_entry)
            db.commit()

            return {
                "account_currency": body.get("accountCurrency"),
                "balance": body.get("balance")
            }

        except (BoAAuthenticationError, BoAAPIError, BoARateLimitError) as e:
            logger.error(f"BoA API error getting balance: {str(e)}")
            raise BoAServiceError(f"Balance fetch failed: {str(e)}")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error saving balance: {str(e)}")
            raise BoAServiceError(f"Database error: {str(e)}")


class BoABankService:
    """Service for bank list operations"""

    @staticmethod
    async def get_bank_list(db: Session) -> List[Dict[str, Any]]:
        """
        Get list of available banks from BoA
        """
        try:
            response = await boa_api.get_bank_list()

            if not response:
                logger.error("Empty response from BoA bank list API")
                return []

            header = response.get("header", {})
            body = response.get("body", [])

            if header.get("status") != "success":
                logger.error(f"BoA bank list API failed: {header}")
                return []

            # Update database with fresh bank list
            # Clear existing banks first
            db.query(BoABankList).delete()

            banks = []
            for bank_data in body:
                bank = BoABankList(
                    bank_id=bank_data.get("id"),
                    institution_name=bank_data.get("institutionName"),
                    is_active=True,
                    last_updated=datetime.utcnow()
                )
                db.add(bank)
                banks.append({
                    "bank_id": bank_data.get("id"),
                    "institution_name": bank_data.get("institutionName")
                })

            db.commit()
            logger.info(f"Successfully updated bank list with {len(banks)} banks")
            return banks

        except (BoAAuthenticationError, BoAAPIError, BoARateLimitError) as e:
            logger.error(f"BoA API error getting bank list: {str(e)}")
            raise BoAServiceError(f"Bank list fetch failed: {str(e)}")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error saving bank list: {str(e)}")
            raise BoAServiceError(f"Database error: {str(e)}")