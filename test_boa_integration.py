#!/usr/bin/env python3
"""
Test script for Bank of Abyssinia API integration
Run this script to test the BoA integration functionality
"""

import asyncio
import os
import sys
from datetime import datetime
from unittest.mock import Mock, patch

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.utils.boa_api_service import BankOfAbyssiniaAPI, BoAAuthenticationError, BoAAPIError
from app.utils.boa_service import (
    BoABeneficiaryService,
    BoATransferService,
    BoAStatusService,
    BoARateService,
    BoABankService,
    BoAServiceError
)
from app.utils.boa_error_handler import BoAErrorHandler, BoAErrorCode
from app.database.database import SessionLocal
from app.models.boa_integration import BoABeneficiaryInquiry
from app.models.transactions import Transaction

class BoATestSuite:
    """Comprehensive test suite for BoA integration"""

    def __init__(self):
        self.test_results = []
        self.db = SessionLocal()

    def log_test_result(self, test_name: str, success: bool, message: str = "", error: str = ""):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)

        status = "PASS" if success else "FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"      {message}")
        if error:
            print(f"      Error: {error}")

    def print_summary(self):
        """Print test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests

        print(f"\n{'='*50}")
        print("TEST SUMMARY")
        print(f"{'='*50}")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "N/A")

        if failed_tests > 0:
            print("\nFAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['error']}")

    async def test_api_service_initialization(self):
        """Test BoA API service initialization"""
        try:
            # Test with missing credentials (should not fail on init)
            api = BankOfAbyssiniaAPI()
            assert api.base_url is not None
            assert api.client is not None
            self.log_test_result("API Service Initialization", True, "Service initialized successfully")
        except Exception as e:
            self.log_test_result("API Service Initialization", False, error=str(e))

    async def test_authentication_with_mock(self):
        """Test authentication with mocked response"""
        try:
            api = BankOfAbyssiniaAPI()

            # Mock successful authentication
            mock_response = {
                "access_token": "test_token_12345",
                "refresh_token": "test_refresh_12345",
                "token_type": "Bearer",
                "expires_in": 7200
            }

            with patch.object(api.client, 'post') as mock_post:
                mock_post.return_value.status_code = 200
                mock_post.return_value.json.return_value = mock_response

                # This should work with mocked credentials
                with patch.dict(os.environ, {
                    'BOA_CLIENT_ID': 'test_client',
                    'BOA_CLIENT_SECRET': 'test_secret',
                    'BOA_REFRESH_TOKEN': 'test_refresh',
                    'BOA_X_API_KEY': 'test_api_key'
                }):
                    await api._authenticate()

                    assert api._access_token == "test_token_12345"
                    assert api._token_expires_at is not None

                    self.log_test_result("Authentication (Mock)", True, "Authentication flow works correctly")

        except Exception as e:
            self.log_test_result("Authentication (Mock)", False, error=str(e))

    async def test_beneficiary_service(self):
        """Test beneficiary service with mocked API"""
        try:
            # Mock the API response
            mock_api_response = {
                "header": {"status": "success"},
                "body": [{"customerName": "John Doe", "accountCurrency": "ETB"}]
            }

            with patch('app.utils.boa_service.boa_api') as mock_boa_api:
                async def mock_fetch_beneficiary_name(account_id):
                    return mock_api_response
                mock_boa_api.fetch_beneficiary_name = mock_fetch_beneficiary_name

                result = await BoABeneficiaryService.fetch_beneficiary_name("123456789", self.db)

                assert result is not None
                assert result["customer_name"] == "John Doe"
                assert result["account_currency"] == "ETB"

                self.log_test_result("Beneficiary Service", True, "Beneficiary lookup works correctly")

        except Exception as e:
            self.log_test_result("Beneficiary Service", False, error=str(e))

    async def test_transfer_service(self):
        """Test transfer service with mocked API"""
        try:
            # Mock the API response
            mock_api_response = {
                "header": {
                    "status": "success",
                    "id": "FT123456789",
                    "uniqueIdentifier": "IRFX123456789",
                    "transactionStatus": "success"
                },
                "body": {
                    "transactionType": "AC",
                    "debitAccountId": "123456",
                    "creditAccountId": "987654",
                    "debitAmount": "100.00",
                    "creditAmount": "100.00",
                    "debitCurrency": "ETB",
                    "creditCurrency": "ETB"
                }
            }

            with patch('app.utils.boa_service.boa_api') as mock_boa_api:
                async def mock_initiate_within_boa_transfer(amount, account_number, reference):
                    return mock_api_response
                mock_boa_api.initiate_within_boa_transfer = mock_initiate_within_boa_transfer

                result = await BoATransferService.initiate_within_boa_transfer(
                    transaction_id=1,
                    amount="100.00",
                    account_number="987654",
                    reference="TEST123",
                    db=self.db
                )

                assert result["success"] is True
                assert result["boa_reference"] == "FT123456789"
                assert result["unique_identifier"] == "IRFX123456789"

                self.log_test_result("Transfer Service", True, "Transfer initiation works correctly")

        except Exception as e:
            self.log_test_result("Transfer Service", False, error=str(e))

    async def test_error_handling(self):
        """Test error handling with various error scenarios"""
        try:
            # Test authentication error
            auth_error = BoAAuthenticationError("Invalid credentials")
            error_info = BoAErrorHandler.handle_boa_exception(auth_error)

            assert error_info["error_code"] == BoAErrorCode.AUTHENTICATION_FAILED.value
            assert error_info["retryable"] is False
            assert error_info["requires_admin_attention"] is True

            # Test API error parsing
            api_error_data = {
                "status": "401",
                "errorDescription": "Client ID is not found"
            }
            error_code, severity, message = BoAErrorHandler.parse_boa_error(api_error_data)

            assert error_code == BoAErrorCode.INVALID_CLIENT_ID
            assert severity == "high"

            # Test business error parsing
            business_error_data = {
                "header": {"status": "failed"},
                "error": {"type": "BUSINESS", "errorDetails": {"code": "E-111450", "message": "Invalid account"}}
            }
            error_code, severity, message = BoAErrorHandler.parse_boa_error(business_error_data)

            assert error_code == BoAErrorCode.BUSINESS_ERROR

            self.log_test_result("Error Handling", True, "Error handling works correctly for various scenarios")

        except Exception as e:
            self.log_test_result("Error Handling", False, error=str(e))

    async def test_currency_rate_service(self):
        """Test currency rate service"""
        try:
            mock_rate_response = {
                "header": {"status": "success"},
                "body": [{
                    "currencyCode": "USD",
                    "currencyName": "US Dollar",
                    "buyRate": "56.8769",
                    "sellRate": "60.0000"
                }]
            }

            with patch('app.utils.boa_service.boa_api') as mock_boa_api:
                async def mock_get_currency_rate(base_currency):
                    return mock_rate_response
                mock_boa_api.get_currency_rate = mock_get_currency_rate

                result = await BoARateService.get_currency_rate("USD", self.db)

                assert result is not None
                assert result["currency_code"] == "USD"
                assert result["buy_rate"] == "56.8769"
                assert result["sell_rate"] == "60.0000"

                self.log_test_result("Currency Rate Service", True, "Currency rate retrieval works correctly")

        except Exception as e:
            self.log_test_result("Currency Rate Service", False, error=str(e))

    async def test_bank_list_service(self):
        """Test bank list service"""
        try:
            mock_bank_response = {
                "header": {"status": "success"},
                "body": [
                    {"id": "231402", "institutionName": "Commercial Bank of Ethiopia"},
                    {"id": "231404", "institutionName": "Awash Bank"}
                ]
            }

            with patch('app.utils.boa_service.boa_api') as mock_boa_api:
                async def mock_get_bank_list():
                    return mock_bank_response
                mock_boa_api.get_bank_list = mock_get_bank_list

                result = await BoABankService.get_bank_list(self.db)

                assert len(result) == 2
                assert result[0]["bank_id"] == "231402"
                assert result[0]["institution_name"] == "Commercial Bank of Ethiopia"

                self.log_test_result("Bank List Service", True, "Bank list retrieval works correctly")

        except Exception as e:
            self.log_test_result("Bank List Service", False, error=str(e))

    async def test_retry_logic(self):
        """Test retry logic for failed operations"""
        try:
            # Test retryable errors
            assert BoAErrorHandler.should_retry(BoAErrorCode.NETWORK_ERROR, 1) is True
            assert BoAErrorHandler.should_retry(BoAErrorCode.NETWORK_ERROR, 3) is False  # Max retries
            assert BoAErrorHandler.should_retry(BoAErrorCode.AUTHENTICATION_FAILED, 1) is False

            # Test retry delays
            delay1 = BoAErrorHandler.get_retry_delay_seconds(BoAErrorCode.NETWORK_ERROR, 1)
            delay2 = BoAErrorHandler.get_retry_delay_seconds(BoAErrorCode.NETWORK_ERROR, 2)

            assert delay2 > delay1  # Exponential backoff

            self.log_test_result("Retry Logic", True, "Retry logic works correctly")

        except Exception as e:
            self.log_test_result("Retry Logic", False, error=str(e))

    async def test_postman_collection_accuracy(self):
        """Test that implementation matches Postman collection exactly"""
        try:
            # Test authentication request structure
            api = BankOfAbyssiniaAPI()

            # Mock the exact authentication request from Postman
            expected_auth_payload = {
                "client_secret": "d44gvjIhns614II5P7Nlrd1SoZ3kg5aB",
                "client_id": "HakimRemitTest",
                "refresh_token": "ElyIydAUfWDbyKPd21mQgj7Giee92se3",
                "grant_type": "refresh_token"
            }

            with patch.object(api.client, 'post') as mock_post:
                mock_post.return_value.status_code = 200
                mock_post.return_value.json.return_value = {
                    "access_token": "test_token",
                    "refresh_token": "new_refresh_token",
                    "token_type": "bearer",
                    "expires_in": 7200
                }

                with patch.dict(os.environ, {
                    'BOA_CLIENT_ID': 'HakimRemitTest',
                    'BOA_CLIENT_SECRET': 'd44gvjIhns614II5P7Nlrd1SoZ3kg5aB',
                    'BOA_REFRESH_TOKEN': 'ElyIydAUfWDbyKPd21mQgj7Giee92se3',
                    'BOA_X_API_KEY': 'W0Suhcd9XjFHmOUJbxMABa2gRyRDpYql0tYyuO5XIzQhgO2SG8Zli52jpZxk7JPi'
                }, clear=True):
                    await api._authenticate()

                    # Verify the request was made correctly
                    mock_post.assert_called_once()
                    call_args = mock_post.call_args

                    # Check URL
                    assert "oauth2/token" in call_args[1]['url']

                    # Check payload
                    actual_payload = call_args[1]['json']
                    assert actual_payload == expected_auth_payload

                    self.log_test_result("Postman Authentication", True, "Authentication matches Postman collection")

        except Exception as e:
            self.log_test_result("Postman Authentication", False, error=str(e))

    async def test_transfer_request_structure(self):
        """Test that transfer requests match Postman collection"""
        try:
            # Test within BoA transfer request structure
            api = BankOfAbyssiniaAPI()

            # Mock the exact transfer request from Postman
            expected_transfer_payload = {
                "client_id": "HakimRemitTest",
                "amount": "100",
                "accountNumber": "7260865",
                "reference": "stringETSW"
            }

            mock_response = {
                "header": {
                    "status": "success",
                    "id": "FT23343L0Z8C",
                    "uniqueIdentifier": "IRFX240244833914396.00",
                    "transactionStatus": "Live"
                },
                "body": {
                    "transactionType": "AC",
                    "debitAccountId": "20654376",
                    "creditAccountId": "7260865",
                    "debitAmount": "100.00",
                    "creditAmount": "100.00",
                    "debitCurrency": "ETB",
                    "creditCurrency": "ETB"
                }
            }

            with patch.object(api.client, 'post') as mock_post:
                mock_post.return_value.status_code = 200
                mock_post.return_value.json.return_value = mock_response

                with patch.dict(os.environ, {
                    'BOA_CLIENT_ID': 'HakimRemitTest',
                    'BOA_CLIENT_SECRET': 'd44gvjIhns614II5P7Nlrd1SoZ3kg5aB',
                    'BOA_REFRESH_TOKEN': 'ElyIydAUfWDbyKPd21mQgj7Giee92se3',
                    'BOA_X_API_KEY': 'W0Suhcd9XjFHmOUJbxMABa2gRyRDpYql0tYyuO5XIzQhgO2SG8Zli52jpZxk7JPi'
                }, clear=True):
                    # Set a dummy access token
                    api._access_token = "njPXnoGx83lpwXAcaPkb6jaNrvwY2iwd"

                    result = await api.initiate_within_boa_transfer(
                        amount="100",
                        account_number="7260865",
                        reference="stringETSW"
                    )

                    # Verify the request was made correctly
                    mock_post.assert_called_once()
                    call_args = mock_post.call_args

                    # Check URL
                    assert "transferWithin" in call_args[1]['url']

                    # Check payload
                    actual_payload = call_args[1]['json']
                    assert actual_payload == expected_transfer_payload

                    # Check headers include x-api-key and Authorization
                    headers = call_args[1]['headers']
                    assert headers.get('x-api-key') == '822a4254-e348-4bc7-bbda-1f0ec79d5eb0'
                    assert headers.get('Authorization') == 'Ersic9oOAWSGvJ5YgVwq1muL7Mfwvqp5'  # No Bearer prefix by default

                    self.log_test_result("Postman Transfer", True, "Transfer request matches Postman collection")

        except Exception as e:
            self.log_test_result("Postman Transfer", False, error=str(e))

    async def run_all_tests(self):
        """Run all tests"""
        print("Starting Bank of Abyssinia API Integration Tests")
        print("=" * 50)

        # Run all test methods
        test_methods = [
            method for method in dir(self)
            if method.startswith('test_') and callable(getattr(self, method))
        ]

        for test_method in test_methods:
            try:
                await getattr(self, test_method)()
            except Exception as e:
                self.log_test_result(test_method, False, error=f"Test execution failed: {str(e)}")

        self.print_summary()

        # Cleanup
        self.db.close()

async def main():
    """Main test function"""
    print("Bank of Abyssinia API Integration Test Suite")
    print("Note: These tests use mocked API responses for safety")
    print("Set actual BoA credentials as environment variables to test with real API")
    print()

    # Check if real credentials are available
    has_real_credentials = all([
        os.getenv('BOA_CLIENT_ID'),
        os.getenv('BOA_CLIENT_SECRET'),
        os.getenv('BOA_REFRESH_TOKEN'),
        os.getenv('BOA_X_API_KEY')
    ])

    if has_real_credentials:
        print("WARNING: Real BoA credentials found! Tests will use actual API.")
        print("   Make sure you're testing in a safe environment.")
        print("   Current Base URL:", os.getenv('BOA_BASE_URL', 'https://boapibeta.bankofabyssinia.com/remittance/hakimRemit'))
    else:
        print("INFO: Using mocked responses for testing.")
        print("   Set BOA_CLIENT_ID, BOA_CLIENT_SECRET, BOA_REFRESH_TOKEN, and BOA_X_API_KEY")
        print("   environment variables to test with real API.")
        print("   Expected Base URL: https://boapibeta.bankofabyssinia.com/remittance/hakimRemit")

    print()

    # Run tests
    test_suite = BoATestSuite()
    await test_suite.run_all_tests()

    return len([r for r in test_suite.test_results if not r["success"]]) == 0

if __name__ == "__main__":
    success = asyncio.run(main())

    exit_code = 0 if success else 1
    sys.exit(exit_code)