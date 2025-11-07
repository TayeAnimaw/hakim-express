#!/usr/bin/env python3
"""
Test script for Bank of Abyssinia API integration with real credentials
Run this script to test the integration with actual BoA API credentials
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent / 'app'))

from app.utils.boa_api_service import boa_api
from app.database.database import SessionLocal

async def test_real_boa_integration():
    """Test the BoA integration with real credentials"""

    print("Testing Bank of Abyssinia API Integration with Real Credentials")
    print("=" * 70)

    # Check if credentials are available
    required_env_vars = [
        'BOA_CLIENT_ID',
        'BOA_CLIENT_SECRET',
        'BOA_REFRESH_TOKEN',
        'BOA_X_API_KEY'
    ]

    missing_vars = [var for var in required_env_vars if not os.getenv(var)]

    if missing_vars:
        print("Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables in your .env file or environment:")
        print("BOA_CLIENT_ID=your_client_id")
        print("BOA_CLIENT_SECRET=your_client_secret")
        print("BOA_REFRESH_TOKEN=your_refresh_token")
        print("BOA_X_API_KEY=your_x_api_key")
        return False

    print("All required credentials are set")

    # Test 1: Authentication
    print("\nTesting Authentication...")
    try:
        access_token = await boa_api._ensure_authenticated()
        print(f"Authentication successful - Token: {access_token[:20]}...")
    except Exception as e:
        print(f"Authentication failed: {str(e)}")
        return False

    # Test 2: Get Bank List
    print("\nTesting Bank List Retrieval...")
    try:
        response = await boa_api.get_bank_list()
        if response and response.get("header", {}).get("status") == "success":
            banks = response.get("body", [])
            print(f"Bank list retrieved successfully - {len(banks)} banks found")
            if banks:
                print(f"   Sample: {banks[0].get('institutionName', 'N/A')}")
        else:
            print("Bank list retrieval failed or returned error")
            return False
    except Exception as e:
        print(f"Bank list test failed: {str(e)}")
        return False

    # Test 3: Currency Rate
    print("\nTesting Currency Rate...")
    try:
        response = await boa_api.get_currency_rate("USD")
        if response and response.get("header", {}).get("status") == "success":
            rate_data = response.get("body", [{}])[0]
            print(f"Currency rate retrieved - USD Buy: {rate_data.get('buyRate', 'N/A')}, Sell: {rate_data.get('sellRate', 'N/A')}")
        else:
            print("Currency rate retrieval failed or returned error")
            return False
    except Exception as e:
        print(f"Currency rate test failed: {str(e)}")
        return False

    # Test 4: Get Balance
    print("\nTesting Balance Inquiry...")
    try:
        response = await boa_api.get_balance()
        if response and response.get("header", {}).get("status") == "success":
            balance_data = response.get("body", {})
            print(f"Balance retrieved - {balance_data.get('balance', 'N/A')} {balance_data.get('accountCurrency', 'N/A')}")
        else:
            print("Balance inquiry failed or returned error")
            return False
    except Exception as e:
        print(f"Balance test failed: {str(e)}")
        return False

    # Test 5: Beneficiary Name Lookup (if you have a test account)
    print("\nTesting Beneficiary Lookup...")
    test_account = os.getenv('BOA_TEST_ACCOUNT')
    if test_account:
        try:
            response = await boa_api.fetch_beneficiary_name(test_account)
            if response and response.get("header", {}).get("status") == "success":
                beneficiary_data = response.get("body", [{}])[0]
                print(f"Beneficiary found - {beneficiary_data.get('customerName', 'N/A')}")
            else:
                print("Beneficiary lookup failed or returned error")
        except Exception as e:
            print(f"Beneficiary test failed: {str(e)}")
    else:
        print("Skipping beneficiary test - no BOA_TEST_ACCOUNT set")

    print("\n" + "=" * 70)
    print("All tests completed successfully!")
    print("\nYour Bank of Abyssinia integration is working correctly.")
    print("You can now use the API endpoints in your FastAPI application.")

    return True

def main():
    """Main function"""
    print("Bank of Abyssinia API Integration - Real Credentials Test")
    print("\nIMPORTANT: Make sure your VPN is connected and IP is whitelisted!")

    # Run the test
    success = asyncio.run(test_real_boa_integration())

    if success:
        print("\nReady to use! Start your FastAPI server:")
        print("   uvicorn main:app --reload")
        print("\nAPI Documentation will be available at:")
        print("   http://localhost:8000/docs")
        print("\nBoA endpoints available at:")
        print("   http://localhost:8000/api/boa/*")
    else:
        print("\nTests failed. Please check your credentials and VPN connection.")
        print("\nTroubleshooting steps:")
        print("1. Verify VPN is connected to BoA network")
        print("2. Confirm your IP is whitelisted by BoA")
        print("3. Check that all credentials are correct")
        print("4. Ensure BOA_BASE_URL is accessible from your network")

    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)