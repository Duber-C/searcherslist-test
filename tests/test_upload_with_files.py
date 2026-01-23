#!/usr/bin/env python3

import requests
import os

def test_multi_source_with_files():
    """Test multi-source extraction with actual files"""
    
    url = "https:/http://localhost:8000/api/multi-source-extraction/"
    
    # Look for test files
    test_files_dir = "/Users/lbz/Documents/ShareHolder/searcherlist/searcher-backend"
    
    resume_file = None
    buyer_profile_file = None
    
    # Check for any .docx files in the current directory
    for file in os.listdir(test_files_dir):
        if file.endswith('.docx'):
            if 'resume' in file.lower() or 'cv' in file.lower():
                resume_file = os.path.join(test_files_dir, file)
            elif 'buyer' in file.lower() or 'profile' in file.lower():
                buyer_profile_file = os.path.join(test_files_dir, file)
    
    print("🧪 Testing multi-source extraction with files...")
    print(f"Resume file: {resume_file}")
    print(f"Buyer profile file: {buyer_profile_file}")
    
    files = {}
    data = {
        'linkedin_url': 'https://linkedin.com/in/johndoe'
    }
    
    # Add files if available
    try:
        if resume_file and os.path.exists(resume_file):
            files['resume'] = open(resume_file, 'rb')
            print(f"✅ Added resume file: {os.path.basename(resume_file)}")
        
        if buyer_profile_file and os.path.exists(buyer_profile_file):
            files['buyer_profile'] = open(buyer_profile_file, 'rb')
            print(f"✅ Added buyer profile file: {os.path.basename(buyer_profile_file)}")
        
        if not files:
            print("⚠️  No test files found, testing with LinkedIn URL only")
        
        # Make the request
        response = requests.post(url, data=data, files=files)
        result = response.json()
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Status: {result.get('status')}")
        print(f"Message: {result.get('message')}")
        
        if response.status_code == 200 and result.get('status') == 'success':
            print("✅ Multi-source extraction with files successful!")
            print(f"Sources processed: {result.get('sources_processed')}")
            print(f"Sources count: {result.get('sources_count')}")
            
            # Check extracted data
            extracted_data = result.get('extracted_data', {})
            print(f"\n📋 Extracted data summary:")
            print(f"Total fields: {len(extracted_data)}")
            
            # Show fields with actual values
            fields_with_values = []
            for field, data_obj in extracted_data.items():
                if isinstance(data_obj, dict) and data_obj.get('value'):
                    if isinstance(data_obj['value'], list):
                        if len(data_obj['value']) > 0:
                            fields_with_values.append(f"{field}: {len(data_obj['value'])} items")
                    else:
                        fields_with_values.append(f"{field}: {str(data_obj['value'])[:50]}...")
            
            print("Fields with extracted values:")
            for field_info in fields_with_values[:10]:  # Show first 10
                print(f"  ✓ {field_info}")
                
        else:
            print(f"❌ Test failed: {result}")
            
    except Exception as e:
        print(f"❌ Error testing endpoint: {e}")
        
    finally:
        # Close files
        for file_obj in files.values():
            if hasattr(file_obj, 'close'):
                file_obj.close()

if __name__ == "__main__":
    test_multi_source_with_files()