#!/usr/bin/env python3

import requests
import os

def test_multi_source_extraction():
    """Test the new multi-source extraction endpoint"""
    
    url = "https:/http://localhost:8000/api/multi-source-extraction/"
    
    # Test with LinkedIn URL only
    print("🧪 Testing multi-source extraction with LinkedIn URL only...")
    
    data = {
        'linkedin_url': 'https://linkedin.com/in/johndoe'
    }
    
    try:
        response = requests.post(url, data=data)
        result = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {result}")
        
        if response.status_code == 200 and result.get('status') == 'success':
            print("✅ Multi-source extraction endpoint is working!")
            print(f"Sources processed: {result.get('sources_processed')}")
            print(f"Sources count: {result.get('sources_count')}")
            
            # Check extracted data structure
            extracted_data = result.get('extracted_data', {})
            print("\n📋 Sample extracted fields:")
            sample_fields = ['first_name', 'last_name', 'linkedin_url', 'background']
            for field in sample_fields:
                if field in extracted_data:
                    print(f"  {field}: {extracted_data[field]}")
        else:
            print(f"❌ Test failed: {result}")
            
    except Exception as e:
        print(f"❌ Error testing endpoint: {e}")

if __name__ == "__main__":
    test_multi_source_extraction()