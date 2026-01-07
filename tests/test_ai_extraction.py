#!/usr/bin/env python3
"""
Test script for AI profile extraction endpoint
"""
import requests
import json

# API endpoint
url = 'http://localhost:8000/api/ai-profile-extraction/'

print("Testing AI profile extraction endpoint...")
print(f"URL: {url}")
print("\n" + "="*50)

try:
    # Make the request
    response = requests.post(url)
    
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
        print("✅ SUCCESS: AI profile extraction endpoint is working!")
    else:
        print(f"❌ ERROR: Request failed with status {response.status_code}")
        
except requests.exceptions.ConnectionError:
    print("❌ CONNECTION ERROR: Could not connect to the server.")
    print("Make sure Django server is running on http://localhost:8000")
except Exception as e:
    print(f"❌ UNEXPECTED ERROR: {str(e)}")