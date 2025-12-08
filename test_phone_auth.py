#!/usr/bin/env python3
"""
Test script for phone authentication endpoints
Usage: python test_phone_auth.py
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"
PHONE_NUMBER = "+33649370470"


def test_phone_signup():
    """Test phone signup endpoint"""
    print("=" * 60)
    print("Testing Phone Signup")
    print("=" * 60)

    url = f"{BASE_URL}/auth/signup-phone"
    payload = {"phone": PHONE_NUMBER}

    print(f"Endpoint: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("\nSending request...\n")

    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"✓ Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Response: {json.dumps(data, indent=2)}")
            print("\n✓ SUCCESS: OTP should be sent to your phone!")
            print("\nNext step: Use the 6-digit OTP code to verify")
            print(f"  POST {BASE_URL}/auth/verify-phone-otp")
            print(f"  Body: {{\"phone\": \"{PHONE_NUMBER}\", \"token\": \"123456\"}}")
            return True
        elif response.status_code == 409:
            print("⚠ Phone number already registered")
            print(f"  Try login instead: POST {BASE_URL}/auth/login-phone")
            return False
        else:
            print("✗ Error Response:")
            try:
                print(json.dumps(response.json(), indent=2))
            except Exception:
                print(response.text)
            return False

    except requests.exceptions.ConnectionError:
        print("✗ ERROR: Cannot connect to server")
        print("\nMake sure the server is running:")
        print("  cd cuistudio-server")
        print("  source venv/bin/activate")
        print("  python main.py")
        return False
    except Exception as e:
        print(f"✗ ERROR: {type(e).__name__}: {str(e)}")
        return False


def test_phone_login():
    """Test phone login endpoint (for existing users)"""
    print("\n" + "=" * 60)
    print("Testing Phone Login (for existing users)")
    print("=" * 60)

    url = f"{BASE_URL}/auth/login-phone"
    payload = {"phone": PHONE_NUMBER}

    print(f"Endpoint: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("\nSending request...\n")

    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"✓ Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Response: {json.dumps(data, indent=2)}")
            print("\n✓ SUCCESS: OTP sent for login!")
            return True
        else:
            print("Response:")
            try:
                print(json.dumps(response.json(), indent=2))
            except Exception:
                print(response.text)
            return False

    except Exception as e:
        print(f"✗ ERROR: {type(e).__name__}: {str(e)}")
        return False


def verify_server_routes():
    """Check if phone auth endpoints are available"""
    print("=" * 60)
    print("Verifying Server Routes")
    print("=" * 60)

    try:
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/openapi.json")
        if response.status_code == 200:
            spec = response.json()
            auth_paths = [p for p in spec.get('paths', {}).keys() if 'auth' in p]

            required_endpoints = [
                '/api/v1/auth/signup-phone',
                '/api/v1/auth/login-phone',
                '/api/v1/auth/verify-phone-otp'
            ]

            print("\nAvailable auth endpoints:")
            for path in sorted(auth_paths):
                print(f"  ✓ {path}")

            print("\nChecking for phone auth endpoints:")
            all_found = True
            for endpoint in required_endpoints:
                if endpoint in spec.get('paths', {}):
                    print(f"  ✓ {endpoint}")
                else:
                    print(f"  ✗ {endpoint} - MISSING!")
                    all_found = False

            if all_found:
                print("\n✓ All phone auth endpoints are registered!")
                return True
            else:
                print("\n✗ Some phone auth endpoints are missing!")
                print("\nThe server needs to be restarted to load new endpoints:")
                print("  1. Stop the current server (Ctrl+C)")
                print("  2. Restart it: python main.py")
                return False
        else:
            print(f"✗ Could not fetch OpenAPI spec (status: {response.status_code})")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


if __name__ == "__main__":
    print("\n🔐 Phone Authentication Test Suite\n")

    # First verify routes are available
    routes_ok = verify_server_routes()

    if not routes_ok:
        print("\n⚠ Please restart the server and run this script again")
        sys.exit(1)

    # Test signup
    print("\n")
    signup_success = test_phone_signup()

    # If signup fails with "already registered", try login
    if not signup_success:
        test_phone_login()

    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)
