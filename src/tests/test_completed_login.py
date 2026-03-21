"""
Test completed profile login flow
"""
import requests

BASE_URL = "http://127.0.0.1:8000/api"

def test_completed_profile_login():
    """Test what happens when a user with completed profile logs in"""
    print("🔐 Testing Completed Profile Login Flow")
    print("=" * 50)
    
    # Use email with completed profile
    test_email = "lbzuluagag+fulltest@gmail.com"
    
    # Step 1: Generate OTP
    print(f"1. 📧 Generating OTP for completed profile: {test_email}")
    otp_response = requests.post(
        f"{BASE_URL}/generate-otp/",
        headers={'Content-Type': 'application/json'},
        json={'email': test_email}
    )
    
    if otp_response.status_code == 200:
        print("   ✅ OTP generated successfully")
        
        # Step 2: Get OTP and verify it
        print("   ⏳ Getting OTP code...")
        # In real scenario, user gets this from email
        # For test, let's get it from the database
        
        import os, sys, django
        sys.path.append('/Users/lbz/Documents/ShareHolder/searcherlist/searcher-backend')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'searcher_api.settings')
        django.setup()
        
        from users.models import OTP
        latest_otp = OTP.objects.filter(email=test_email).order_by('-created_at').first()
        
        if latest_otp:
            otp_code = latest_otp.otp_code
            print(f"   🔑 OTP Code: {otp_code}")
            
            # Step 3: Verify OTP
            print(f"\n2. 🔐 Verifying OTP for completed profile...")
            verify_response = requests.post(
                f"{BASE_URL}/verify-otp-status/",
                headers={'Content-Type': 'application/json'},
                json={'email': test_email, 'otp_code': otp_code}
            )
            
            print(f"   📊 Status: {verify_response.status_code}")
            verify_result = verify_response.json()
            print(f"   📋 Response: {verify_result}")
            
            if verify_response.status_code == 200 and verify_result.get('success'):
                account_status = verify_result.get('account_status')
                next_action = verify_result.get('next_action')
                
                print(f"\n3. 🎯 Login Decision:")
                print(f"   Account Status: {account_status}")
                print(f"   Next Action: {next_action}")
                
                if account_status == 'finished' and next_action == 'login':
                    print("   ✅ CORRECT: User should go to dashboard!")
                    print("   🏠 Frontend should redirect to /dashboard")
                elif account_status == 'incomplete':
                    print("   ⚠️  User marked as incomplete - should go to profile completion")
                elif account_status == 'new':
                    print("   ❌ ERROR: Existing user marked as new!")
                else:
                    print(f"   ❓ Unknown status: {account_status}")
            else:
                print(f"   ❌ OTP verification failed: {verify_result}")
        else:
            print("   ❌ Could not find OTP in database")
    else:
        print(f"   ❌ Failed to generate OTP: {otp_response.json()}")

if __name__ == "__main__":
    test_completed_profile_login()