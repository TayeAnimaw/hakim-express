# app/utils/boa_api_service.py

import httpx
import asyncio
import os
import time
import json
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class BoAAuthenticationError(Exception):
    """Raised when BoA API authentication fails"""
    pass

class BoAAPIError(Exception):
    """Raised when BoA API returns an error"""
    pass

class BoARateLimitError(Exception):
    """Raised when BoA API rate limit is exceeded"""
    pass

class BankOfAbyssiniaAPI:
    """
    Bank of Abyssinia API service client for remittance integration.
    Handles OAuth 2.0 authentication and all API endpoints.
    """

    def __init__(self):
        self.base_url = settings.BOA_BASE_URL
        self.client_id = settings.BOA_CLIENT_ID
        self.client_secret = settings.BOA_CLIENT_SECRET
        self.api_key = settings.BOA_X_API_KEY
        self.token_file = settings.BOA_TOKEN_FILE
        self.auth_prefix = settings.BOA_AUTH_PREFIX
        token_data = self._load_token_file()
        if token_data and "refresh_token" in token_data:
            self.refresh_token = token_data["refresh_token"]
        else:
            self.refresh_token = settings.BOA_REFRESH_TOKEN
        
        # Token management
        self._access_token = None
        self._token_expires_at = None
        self._token_cache = {}

        # HTTP client with connection pooling
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
            event_hooks={
                "request": [self._log_request_url]
            }
        )
    def update_refresh_token(self, new_refresh_token: str) -> None:
        """update the refresh token in memory"""
        self.refresh_token = new_refresh_token
        
    async def __aenter__(self):
        return self
    async def _log_request_url(self, request: httpx.Request):
        logger.debug(f"BOA request url: {request.url}")

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    def _load_token_file(self) -> Optional[Dict[str, Any]]:
        """Load token from file cache"""
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, "r") as f:
                    data = json.load(f)
                    return data
        except Exception as e:
            logger.warning(f"Failed to load token file: {e}")
        return None

    def _save_token_file(self, data: Dict[str, Any]) -> None:
        """Save token to file cache"""
        try:
            os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
            with open(self.token_file, "w") as f:
                json.dump(data, f)
        except Exception as e:
            logger.warning(f"Failed to save token file: {e}")

    def _is_token_valid(self, token_data: Dict[str, Any]) -> bool:
        """Check if token is valid (with 30 second buffer)"""
        if not token_data:
            return False
        exp = token_data.get("expires_at", 0)
        return time.time() < (exp - 30)

    async def _ensure_authenticated(self) -> str:
        """Ensure we have a valid access token"""

        if self._token_cache and self._is_token_valid(self._token_cache):
            return self._token_cache["access_token"]

        # Check file cache
        disk_token = self._load_token_file()
        if disk_token and self._is_token_valid(disk_token):
            self._token_cache.update(disk_token)
            return disk_token["access_token"]

        # Request new token
        await self._authenticate()
        return self._token_cache["access_token"]

    async def _authenticate(self) -> None:
        """Authenticate with BoA API using OAuth 2.0"""
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            raise BoAAuthenticationError("Missing required BoA API credentials")

        token_url = f"{self.base_url}/oauth2/token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }

        try:
            # Use a separate client for token request to avoid base_url issues
            async with httpx.AsyncClient(timeout=30.0) as token_client:
                response = await token_client.post(
                    token_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                token_data = response.json()

                access_token = token_data.get("access_token")
                refresh_token = token_data.get("refresh_token", self.refresh_token)
                expires_in = int(token_data.get("expires_in", 3600))

                # Create token data with expiration timestamp
                token_info = {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "expires_at": int(time.time()) + expires_in
                }

                # Cache in memory and save to file
                self._token_cache.update(token_info)
                self.update_refresh_token(refresh_token)
                self._save_token_file(token_info)

                logger.info("Successfully authenticated with Bank of Abyssinia API")

        except httpx.HTTPStatusError as e:
            logger.error(f"BoA authentication failed: {e.response.status_code} - {e.response.text}")
            if e.response.status_code == 401:
                raise BoAAuthenticationError(f"Authentication failed: {e.response.text}")
            else:
                raise BoAAPIError(f"Token request failed: {e.response.text}")
        except Exception as e:
            logger.error(f"Unexpected error during BoA authentication: {str(e)}")
            raise BoAAPIError(f"Authentication error: {str(e)}")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        include_auth: bool = True
    ) -> Dict[str, Any]:
        """Make authenticated request to BoA API"""

        if include_auth:
            access_token = await self._ensure_authenticated()

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key
        }

        if include_auth and access_token:
            headers["Authorization"] = f"{self.auth_prefix}{access_token}"

        try:
            response = await self.client.request(
                method=method,
                url=endpoint,
                json=data,
                params=params,
                headers=headers
            )

            # DO NOT raise_for_status → BoA returns JSON even on 400/404/401
            result = response.json()
            result["http_status"] = response.status_code  # keep original status
            return result

        except httpx.RequestError as e:
            logger.error(f"BoA network error: {str(e)}")
            return {
                "header": {
                    "status": "failed",
                    "code": 500,
                    "message": "Network error contacting BOA"
                },
                "body": None,
                "http_status": 500
            }


    # API Methods based on documentation

    async def get_access_token(self) -> Dict[str, Any]:
        """Get new access token using refresh token"""
        return await self._authenticate()

    async def fetch_beneficiary_name(self, account_id: str) -> Dict[str, Any]:
        """Fetch beneficiary name for BoA account"""
        endpoint = f"getAccount/{account_id}"
        return await self._make_request("GET", endpoint)

    async def fetch_beneficiary_name_other_bank(self, bank_id: str, account_id: str) -> Dict[str, Any]:
        """Fetch beneficiary name for other bank account"""
        endpoint = f"otherBank/getAccount/{bank_id}/{account_id}"
        return await self._make_request("GET", endpoint)

    async def initiate_within_boa_transfer(
        self,
        amount: str,
        account_number: str,
        reference: str
    ) -> Dict[str, Any]:
        """Initiate transfer within Bank of Abyssinia"""
        endpoint = "transferWithin"
        data = {
            "client_id": self.client_id,
            "amount": amount,
            "accountNumber": account_number,
            "reference": reference
        }
        return await self._make_request("POST", endpoint, data=data)

    async def get_bank_list(self) -> Dict[str, Any]:
        """Get list of available banks for other bank transfers"""
        endpoint = "otherBank/bankId"
        return await self._make_request("GET", endpoint)

    async def initiate_other_bank_transfer(
        self,
        amount: str,
        bank_code: str,
        account_number: str,
        reference: str,
        receiver_name: str
    ) -> Dict[str, Any]:
        """Initiate transfer to other bank using EthSwitch"""
        endpoint = "otherBank/transferEthswitch"
        data = {
            "client_id": self.client_id,
            "amount": amount,
            "bankCode": bank_code,
            "receiverName": receiver_name,
            "accountNumber": account_number,
            "reference": reference
        }
        return await self._make_request("POST", endpoint, data=data)

    async def check_transaction_status(self, transaction_id: str) -> Dict[str, Any]:
        """Check status of a transaction"""
        endpoint = f"transactionStatus/{transaction_id}"
        return await self._make_request("GET", endpoint)

    async def get_currency_rate(self, base_currency: str) -> Dict[str, Any]:
        """Get currency exchange rate"""
        endpoint = f"rate/{base_currency}"
        return await self._make_request("GET", endpoint)

    async def get_balance(self) -> Dict[str, Any]:
        """Get remitter account balance"""
        endpoint = "getBalance"
        data = {
            "client_id": self.client_id
        }
        return await self._make_request("POST", endpoint, data=data)

    async def initiate_money_send(
        self,
        amount: str,
        remitter_name: str,
        remitter_phone: str,
        receiver_name: str,
        receiver_address: str,
        receiver_phone: str,
        reference: str,
        secret_code: str
    ) -> Dict[str, Any]:
        """Initiate money send (wallet transfer)"""
        endpoint = "moneySend"
        data = {
            "client_id": self.client_id,
            "amount": amount,
            "remitterName": remitter_name,
            "remitterPhonenumber": remitter_phone,
            "receiverName": receiver_name,
            "receiverAddress": receiver_address,
            "receiverPhonenumber": receiver_phone,
            "reference": reference,
            "secretCode": secret_code
        }
        return await self._make_request("POST", endpoint, data=data)

# Global instance for dependency injection
boa_api = BankOfAbyssiniaAPI()
