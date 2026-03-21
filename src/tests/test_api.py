"""
Test script to verify Django API endpoints are working
Run this with: python test_api.py
"""

import requests
import json
from io import BytesIO

# API base URL
BASE_URL = "http://127.0.0.1:8000/api"

def test_health_check():
    """Test the health check endpoint"""
    print("Testing health check endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health/")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_create_profile():
    """Test creating a user profile"""
    print("\nTesting profile creation endpoint...")
    
    # Sample form data matching your React form
    data = {
        'username': 'johndoe',
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john.doe@example.com',
        'phone_number': '+1234567890',
        'country': 'United States',
        'city': 'New York',
        'state': 'NY',
        'linkedin_url': 'https://linkedin.com/in/johndoe',
        'background': 'I am an experienced business professional with over 10 years in the industry. Looking to acquire a business in the tech sector with revenue between 1-5 million. I have experience in operations, finance, and strategic planning.'
    }
    
    try:
        response = requests.post(f"{BASE_URL}/create-profile/", data=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 201
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_create_profile_with_files():
    """Test creating a profile with file uploads"""
    print("\nTesting profile creation with files...")
    
    # Sample form data
    data = {
        'username': 'janesmith',
        'first_name': 'Jane',
        'last_name': 'Smith',
        'email': 'jane.smith@example.com',
        'phone_number': '+1987654321',
        'country': 'Canada',
        'city': 'Toronto',
        'state': 'ON',
        'linkedin_url': 'https://linkedin.com/in/janesmith',
        'background': 'Experienced finance professional seeking to acquire a manufacturing business. I have 15+ years of experience in financial analysis, due diligence, and business operations. Looking for opportunities in the 2-10 million revenue range.'
    }
    
    # Create dummy files
    files = {
        'resume': ('resume.txt', BytesIO(b'This is a dummy resume file'), 'text/plain'),
        'buyer_profile': ('profile.txt', BytesIO(b'This is a dummy buyer profile file'), 'text/plain')
    }
    
    try:
        response = requests.post(f"{BASE_URL}/create-profile/", data=data, files=files)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 201
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Django API Test Suite")
    print("=" * 50)
    
    # Run tests
    tests_passed = 0
    total_tests = 3
    
    if test_health_check():
        tests_passed += 1
    
    if test_create_profile():
        tests_passed += 1
    
    if test_create_profile_with_files():
        tests_passed += 1
    
    print("\n" + "=" * 50)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("✅ All tests passed! Your Django API is working correctly.")
    else:
        print("❌ Some tests failed. Check your Django server and configuration.")