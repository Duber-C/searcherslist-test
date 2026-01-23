#!/usr/bin/env python3
"""
Test script for basic-info endpoint
"""
import requests
import json

# Test data from the form
test_data = {
    'email': 'lbzuluagag+fulltest@gmail.com',  # Using existing email from database
    'firstName': 'luis',
    'lastName': 'zuluaga', 
    'phoneNumber': '+573217598863',
    'linkedinUrl': 'https://www.linkedin.com/in/luis-bernardo-zuluaga-gomez-859431218/',
    'website': 'a.com',
    'languages': 'a'
}

# API endpoint
url = 'https:/http://localhost:8000/api/update-basic-info/'

print("Testing basic-info endpoint with data:")
print(json.dumps(test_data, indent=2))
print("\n" + "="*50)

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
        
    print("\n" + "="*50)
    
    if response.status_code == 200:
        print("✅ SUCCESS: Basic info updated successfully!")
    else:
        print(f"❌ ERROR: Request failed with status {response.status_code}")
        
except requests.exceptions.ConnectionError:
    print("❌ CONNECTION ERROR: Could not connect to the server.")
    print("Make sure Django server is running on https:/http://localhost:8000")
except Exception as e:
    print(f"❌ UNEXPECTED ERROR: {str(e)}")