"""
Test OTP functionality
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api"

def test_send_otp_new_user():
    """Test sending OTP to new user"""
    print("Testing OTP for new user...")
    
    data = {
        'email': 'lbzuluagag+1@gmail.com'
    }
    
    try:
        response = requests.post(f"{BASE_URL}/send-otp/", data=data)
        result = response.json()
        print(f"Status: {response.status_code}")
        print(f"Response: {result}")
        return response.status_code == 200 and result.get('success', False)
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_send_otp_existing_user():
    """Test sending OTP to existing user"""
    print("\nTesting OTP for existing user...")
    
    data = {
        'email': 'lbzuluagag+2@gmail.com'  # This user was created in previous tests
    }
    
    try:
        response = requests.post(f"{BASE_URL}/send-otp/", data=data)
        result = response.json()
        print(f"Status: {response.status_code}")
        print(f"Response: {result}")
        return response.status_code == 200 and result.get('success', False)
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_verify_otp_invalid():
    """Test verifying invalid OTP"""
    print("\nTesting invalid OTP verification...")
    
    data = {
        'email': 'lbzuluagag+1@gmail.com',
        'otp_code': '123456'  # Wrong OTP
    }
    
    try:
        response = requests.post(f"{BASE_URL}/verify-otp/", data=data)
        result = response.json()
        print(f"Status: {response.status_code}")
        print(f"Response: {result}")
        return response.status_code == 400 and not result.get('success', True)
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("OTP System Test Suite")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    if test_send_otp_new_user():
        tests_passed += 1
    
    if test_send_otp_existing_user():
        tests_passed += 1
    
    if test_verify_otp_invalid():
        tests_passed += 1
    
    print("\n" + "=" * 50)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("✅ All OTP tests passed!")
        print("\nNote: Check your terminal running the Django server to see the OTP codes")
        print("(since we're using console email backend for development)")
    else:
        print("❌ Some OTP tests failed.")