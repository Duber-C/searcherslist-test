"""
Test OTP verification with real code from server output
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api"

def test_verify_real_otp():
    """Test verifying the actual OTP code from server output"""
    print("Testing OTP verification with real code...")
    
    # Using the actual OTP code from your server output: 392870
    data = {
        'email': 'lbzuluagag+2@gmail.com',
        'otp_code': '392870'
    }
    
    try:
        response = requests.post(f"{BASE_URL}/verify-otp/", data=data)
        result = response.json()
        print(f"Status: {response.status_code}")
        print(f"Response: {result}")
        return response.status_code == 200 and result.get('success', False)
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Real OTP Verification Test")
    print("=" * 40)
    
    if test_verify_real_otp():
        print("✅ OTP verification successful!")
    else:
        print("❌ OTP verification failed.")