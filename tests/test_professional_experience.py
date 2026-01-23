#!/usr/bin/env python3
"""
Test script for professional-experience endpoint
"""
import requests
import json

# Test data for professional experience
test_data = {
    'email': 'lbzuluagag+4@gmail.com',
    'currentRole': 'Senior Analyst',
    'company': 'Test Company Inc.',
    'yearsExperience': '5+ years',
    'bio': 'Test bio for professional experience',
    'investmentExperience': '3 years',
    'dealSizePreference': '$1M-$10M',
    'industryFocus': 'Technology, Healthcare',
    'geographicFocus': 'North America'
}

# Test both the individual endpoint and the generic section endpoint
endpoints = [
    ('Individual Endpoint', 'https://api.searcherlist.com/api/update-professional-experience/'),
    ('Section Endpoint', 'https://api.searcherlist.com/api/update-profile/professional-experience/')
]

for endpoint_name, url in endpoints:
    print(f"\n{'='*20} {endpoint_name} {'='*20}")
    print(f"Testing: {url}")
    print("Data:", json.dumps(test_data, indent=2))
    
    try:
        # Make the request
        response = requests.patch(url, json=test_data)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print("\nResponse Body:")
        
        try:
            response_json = response.json()
            print(json.dumps(response_json, indent=2))
        except:
            print(response.text)
            
        if response.status_code == 200:
            print("✅ SUCCESS: Professional experience updated successfully!")
        else:
            print(f"❌ ERROR: Request failed with status {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Could not connect to the server.")
        print("Make sure Django server is running on https://api.searcherlist.com")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {str(e)}")

print(f"\n{'='*60}")
print("Test completed for both endpoints")