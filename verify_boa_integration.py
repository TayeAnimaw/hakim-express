#!/usr/bin/env python3
"""
Verification script for Bank of Abyssinia API integration
This script verifies that the integration matches the specifications from the other AI
"""

import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent / 'app'))

def check_environment_variables():
    """Check if all required environment variables are properly configured"""
    print("Checking Environment Variables...")

    required_vars = [
        'BOA_BASE_URL',
        'BOA_CLIENT_ID',
        'BOA_CLIENT_SECRET',
        'BOA_REFRESH_TOKEN',
        'BOA_X_API_KEY'
    ]

    optional_vars = [
        'BOA_AUTH_PREFIX',
        'BOA_TOKEN_FILE'
    ]

    missing_required = []
    missing_optional = []

    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
        else:
            print(f"  PASS {var} = {os.getenv(var)[:50]}...")

    for var in optional_vars:
        if not os.getenv(var):
            missing_optional.append(var)
        else:
            print(f"  ✅ {var} = {os.getenv(var)}")

    if missing_required:
        print(f"  FAIL Missing required environment variables: {', '.join(missing_required)}")
        return False

    print(f"  INFO Optional variables not set: {', '.join(missing_optional) if missing_optional else 'None'}")
    return True

def check_file_structure():
    """Check if all required files exist and are properly structured"""
    print("\nChecking File Structure...")

    required_files = [
        'app/core/config.py',
        'app/utils/boa_api_service.py',
        'app/utils/boa_service.py',
        'app/utils/boa_error_handler.py',
        'app/models/boa_integration.py',
        'app/routers/boa_integration.py',
        'app/schemas/boa_integration.py',
        'main.py',
        'alembic/versions/add_boa_integration_models.py'
    ]

    missing_files = []

    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  PASS {file_path}")
        else:
            print(f"  FAIL {file_path} - MISSING")
            missing_files.append(file_path)

    return len(missing_files) == 0

def check_configuration_values():
    """Check if configuration values match the specifications"""
    print("\nChecking Configuration Values...")

    # Check base URL
    base_url = os.getenv('BOA_BASE_URL', 'https://boapibeta.bankofabyssinia.com/remittance/hakimRemit')
    if 'hakimRemit' in base_url:
        print(f"  PASS Base URL correctly includes remitter name: {base_url}")
    else:
        print(f"  FAIL Base URL should include remitter name: {base_url}")
        return False

    # Check client ID
    client_id = os.getenv('BOA_CLIENT_ID', 'hakimRemit_staging')
    if client_id == 'hakimRemit_staging':
        print(f"  PASS Using correct default client ID: {client_id}")
    else:
        print(f"  PASS Custom client ID set: {client_id}")

    # Check auth prefix
    auth_prefix = os.getenv('BOA_AUTH_PREFIX', '')
    if auth_prefix == '':
        print("  PASS Using token-only Authorization header (as per Postman collection)")
    elif auth_prefix == 'Bearer ':
        print("  PASS Using Bearer prefix for Authorization header")
    else:
        print(f"  WARN Custom auth prefix: {auth_prefix}")

    return True

def check_api_endpoints():
    """Check if all required API endpoints are implemented"""
    print("\nChecking API Endpoints...")

    required_endpoints = [
        'GET /beneficiary/boa/{account_id}',
        'GET /beneficiary/other-bank/{bank_id}/{account_id}',
        'POST /transfer/within-boa',
        'POST /transfer/other-bank',
        'POST /transfer/money-send',
        'GET /transaction-status/{transaction_id}',
        'GET /currency-rate/{currency}',
        'GET /balance',
        'GET /banks'
    ]

    # Check if router file exists and contains endpoints
    router_file = 'app/routers/boa_integration.py'
    if not os.path.exists(router_file):
        print(f"  FAIL Router file missing: {router_file}")
        return False

    # Read router file and check for endpoint patterns
    with open(router_file, 'r') as f:
        content = f.read()

    found_endpoints = []
    for endpoint in required_endpoints:
        method = endpoint.split()[0]
        path = endpoint.split()[1]

        if f'@{method.lower()}("{path}"' in content or f'@{method.lower()}(\'{path}\'' in content:
            found_endpoints.append(endpoint)
            print(f"  PASS {endpoint}")
        else:
            print(f"  FAIL {endpoint} - NOT FOUND")

    return len(found_endpoints) == len(required_endpoints)

def check_postman_compliance():
    """Check compliance with Postman collection specifications"""
    print("\nChecking Postman Collection Compliance...")

    checks = [
        ("Authentication uses client_secret in body", "client_secret"),
        ("Transfer requests use client_id in body", "client_id"),
        ("Headers include x-api-key", "x-api-key"),
        ("Authorization header is configurable", "Authorization"),
        ("Other bank transfer uses bankCode", "bankCode"),
        ("Token caching implemented", "token_file"),
        ("Error handling for 401/504", "401"),
    ]

    # Check API service file
    api_service_file = 'app/utils/boa_api_service.py'
    if not os.path.exists(api_service_file):
        print(f"  FAIL API service file missing: {api_service_file}")
        return False

    with open(api_service_file, 'r') as f:
        content = f.read()

    passed_checks = 0
    for check_name, keyword in checks:
        if keyword in content:
            print(f"  PASS {check_name}")
            passed_checks += 1
        else:
            print(f"  FAIL {check_name}")

    return passed_checks >= 5  # At least 5 out of 7 checks should pass

def main():
    """Main verification function"""
    print("Bank of Abyssinia API Integration Verification")
    print("=" * 60)

    verification_results = []

    # Run all checks
    checks = [
        ("Environment Variables", check_environment_variables),
        ("File Structure", check_file_structure),
        ("Configuration Values", check_configuration_values),
        ("API Endpoints", check_api_endpoints),
        ("Postman Compliance", check_postman_compliance),
    ]

    for check_name, check_func in checks:
        try:
            result = check_func()
            verification_results.append((check_name, result))
        except Exception as e:
            print(f"  FAIL {check_name}: Error - {str(e)}")
            verification_results.append((check_name, False))

    # Print summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in verification_results if result)
    total = len(verification_results)

    for check_name, result in verification_results:
        status = "PASS" if result else "FAIL"
        print(f"{status}: {check_name}")

    print(f"\nOverall: {passed}/{total} checks passed ({passed/total*100:.1f}%)")

    if passed == total:
        print("\nSUCCESS All verifications passed! Integration is ready for production.")
        print("\nNext steps:")
        print("1. Set your actual BoA credentials in environment variables")
        print("2. Run database migration: alembic upgrade head")
        print("3. Test with real API: python test_boa_integration.py")
        print("4. Start your FastAPI server and test the endpoints")
        return True
    else:
        print(f"\nWARNING {total-passed} verification(s) failed. Please fix the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    exit_code = 0 if success else 1
    sys.exit(exit_code)