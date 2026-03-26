"""
Test existing user update scenario
"""
import requests

BASE_URL = "http://127.0.0.1:8000/api"

def test_existing_user_update():
    """Test updating an existing user profile"""
    print("🔄 Testing Existing User Update")
    print("=" * 40)
    
    # Use the same email from previous test (user already exists)
    test_email = "lbzuluagag+fulltest@gmail.com"
    
    # Update with new information
    updated_data = {
        'email': test_email,
        'email_verified': 'true',
        'firstName': 'John',
        'lastName': 'Smith',  # Changed last name
        'phoneNumber': '+1987654321',  # Changed phone
        'country': 'Canada',  # Changed country
        'city': 'Toronto',  # Changed city
        'state': 'ON',  # Changed state
        'linkedinUrl': 'https://www.linkedin.com/in/johnsmith-updated',  # Updated LinkedIn
        'background': 'Updated background: Senior executive with 15 years experience in mergers and acquisitions.'
    }
    
    print("📝 Updating existing profile...")
    response = requests.post(f"{BASE_URL}/create-profile/", data=updated_data)
    
    print(f"📊 Status: {response.status_code}")
    result = response.json()
    print(f"📋 Response: {result}")
    
    if response.status_code == 201:
        print("✅ Profile updated successfully!")
        
        # Verify the updates
        get_response = requests.get(f"{BASE_URL}/get-profile/", params={'email': test_email})
        
        if get_response.status_code == 200:
            profile_data = get_response.json()
            data = profile_data.get('data', {})
            
            print("🔍 Verifying updates:")
            print(f"   Last Name: {data.get('lastName')} (should be 'Smith')")
            print(f"   Phone: {data.get('phoneNumber')} (should be '+1987654321')")
            print(f"   City: {data.get('city')} (should be 'Toronto')")
            print(f"   Country: {data.get('country')} (should be 'Canada')")
            
            if (data.get('lastName') == 'Smith' and 
                data.get('phoneNumber') == '+1987654321' and
                data.get('city') == 'Toronto' and
                data.get('country') == 'Canada'):
                print("✅ ALL UPDATES VERIFIED!")
            else:
                print("❌ Some updates failed!")
        
    else:
        print(f"❌ Update failed: {result}")

if __name__ == "__main__":
    test_existing_user_update()