#!/usr/bin/env python3
"""
Test script for AI profile extraction endpoint with file upload
"""
import requests
import json
import os

# API endpoint
url = 'https://api.searcherlist.com/api/ai-profile-extraction/'

print("Testing AI profile extraction endpoint with file upload...")
print(f"URL: {url}")
print("\n" + "="*50)

# Test with a sample DOCX file (create a simple test file)
test_file_path = '/Users/lbz/Documents/ShareHolder/searcherlist/searcher-backend/ai_profile_creation/Grant Williams FINAL BUYER PROFILE - Cohort 59.docx'

if os.path.exists(test_file_path):
    try:
        with open(test_file_path, 'rb') as file:
            files = {'file': (os.path.basename(test_file_path), file, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
            
            print(f"Uploading file: {os.path.basename(test_file_path)}")
            response = requests.post(url, files=files)
        
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
            print("✅ SUCCESS: File upload and AI extraction working!")
        else:
            print(f"❌ ERROR: Request failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
else:
    print(f"❌ Test file not found: {test_file_path}")
    print("Testing with no file (should use sample text)...")
    
    try:
        response = requests.post(url)
        
        print(f"Status Code: {response.status_code}")
        print("Response Body:")
        
        try:
            response_json = response.json()
            print(json.dumps(response_json, indent=2))
        except:
            print(response.text)
            
        if response.status_code == 200:
            print("✅ SUCCESS: Sample text processing working!")
        else:
            print(f"❌ ERROR: Request failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")