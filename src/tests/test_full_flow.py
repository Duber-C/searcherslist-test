"""
Comprehensive test for frontend-backend field compatibility
Tests all fields that the frontend sends to ensure backend receives them correctly
"""
import requests
import json
import os

BASE_URL = "http://127.0.0.1:8000/api"

def test_all_frontend_fields():
    """Test all fields from the frontend ProfileForm"""
    print("🧪 Frontend-Backend Field Compatibility Test")
    print("=" * 60)
    
    # Test email that's already verified via OTP
    test_email = "lbzuluagag+fulltest@gmail.com"
    
    # Step 1: Generate OTP first
    print(f"1. 📧 Generating OTP for: {test_email}")
    otp_response = requests.post(
        f"{BASE_URL}/generate-otp/",
        headers={'Content-Type': 'application/json'},
        json={'email': test_email}
    )
    
    if otp_response.status_code == 200:
        print("   ✅ OTP generated successfully")
        
        # Get the OTP code from database (for testing)
        print("   ⏳ Getting OTP from server...")
        # In a real scenario, user would get this from email
        
    else:
        print(f"   ❌ Failed to generate OTP: {otp_response.json()}")
        return
    
    # Step 2: Create comprehensive profile data matching frontend form
    print(f"\n2. 📝 Testing comprehensive profile creation...")
    
    # Create form data exactly as frontend sends (camelCase)
    form_data = {
        # Email (verified)
        'email': test_email,
        'email_verified': 'true',
        
        # Personal Information (camelCase as frontend sends)
        'firstName': 'John',
        'lastName': 'Doe',
        'phoneNumber': '+1234567890',
        
        # Location
        'country': 'United States',
        'city': 'New York',
        'state': 'NY',
        
        # LinkedIn
        'linkedinUrl': 'https://www.linkedin.com/in/johndoe',
        
        # Background
        'background': 'Experienced business professional with over 10 years in acquisitions and private equity. Looking for manufacturing businesses in the $1-5M range with strong cash flow and growth potential. Particular interest in B2B service companies and light manufacturing in the Northeast region.'
    }
    
    print("   📋 Form data prepared:")
    for key, value in form_data.items():
        print(f"      {key}: {value}")
    
    # Step 3: Test profile creation
    print(f"\n3. 🚀 Sending profile data to backend...")
    
    profile_response = requests.post(
        f"{BASE_URL}/create-profile/",
        data=form_data  # Using form data like the frontend
    )
    
    print(f"   📊 Response Status: {profile_response.status_code}")
    response_data = profile_response.json()
    print(f"   📋 Response Data: {json.dumps(response_data, indent=2)}")
    
    if profile_response.status_code == 201:
        print("   ✅ Profile created successfully!")
        print(f"   👤 Profile ID: {response_data.get('profile_id')}")
        print(f"   ✨ Profile Completed: {response_data.get('profile_completed')}")
        
        # Step 4: Test getting profile data back
        print(f"\n4. 🔍 Testing profile retrieval...")
        get_response = requests.get(
            f"{BASE_URL}/get-profile/",
            params={'email': test_email}
        )
        
        if get_response.status_code == 200:
            profile_data = get_response.json()
            print("   ✅ Profile retrieved successfully!")
            print(f"   📊 Retrieved Data: {json.dumps(profile_data, indent=2)}")
            
            # Verify all fields were saved correctly
            print(f"\n5. 🔎 Field Verification:")
            saved_data = profile_data.get('data', {})
            
            field_mapping = {
                'firstName': 'John',
                'lastName': 'Doe', 
                'phoneNumber': '+1234567890',
                'country': 'United States',
                'city': 'New York',
                'state': 'NY',
                'linkedinUrl': 'https://www.linkedin.com/in/johndoe'
            }
            
            all_correct = True
            for frontend_field, expected_value in field_mapping.items():
                actual_value = saved_data.get(frontend_field)
                if actual_value == expected_value:
                    print(f"   ✅ {frontend_field}: {actual_value}")
                else:
                    print(f"   ❌ {frontend_field}: Expected '{expected_value}', got '{actual_value}'")
                    all_correct = False
            
            # Check background separately (longer text)
            background_saved = saved_data.get('background', '')
            if len(background_saved) > 50:
                print(f"   ✅ background: {background_saved[:50]}...")
            else:
                print(f"   ❌ background: Too short or missing")
                all_correct = False
            
            print(f"\n📊 Overall Result: {'✅ ALL TESTS PASSED' if all_correct else '❌ SOME TESTS FAILED'}")
            
        else:
            print(f"   ❌ Failed to retrieve profile: {get_response.json()}")
    
    else:
        print("   ❌ Profile creation failed!")
        if 'errors' in response_data:
            print("   📝 Validation Errors:")
            for field, errors in response_data['errors'].items():
                print(f"      {field}: {errors}")
        
        if 'debug_info' in response_data:
            print("   🔍 Debug Info:")
            for key, value in response_data['debug_info'].items():
                print(f"      {key}: {value}")

if __name__ == "__main__":
    test_all_frontend_fields()