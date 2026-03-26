#!/usr/bin/env python3

"""
Test script to reproduce multi-source extraction issue with LinkedIn + Buyer Profile
"""

import sys
import os
sys.path.append('/Users/lbz/Documents/ShareHolder/searcherlist/searcher-backend')

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')
import django
django.setup()

def test_multi_source_with_files():
    from linkedIn_extraction import run_linkedin_extraction
    from ai_profile_creation.chatGpt import extract_profile_from_multiple_sources, extract_text_from_docx
    import json

    print("🧪 TESTING MULTI-SOURCE: LinkedIn + Buyer Profile")
    print("=" * 60)
    
    # Grant Williams LinkedIn URL
    linkedin_url = 'https://www.linkedin.com/in/grant-nelson-williams/'
    
    # Use actual Grant Williams buyer profile file
    grant_williams_file = "/Users/lbz/Documents/ShareHolder/searcherlist/searcher-backend/ai_profile_creation/Grant Williams FINAL BUYER PROFILE - Cohort 59.docx"
    
    print(f"📄 Extracting text from Grant Williams file: {grant_williams_file}")
    try:
        buyer_profile_text = extract_text_from_docx(grant_williams_file)
        print(f"✅ File extraction successful - {len(buyer_profile_text)} characters")
        print(f"📝 Preview: {buyer_profile_text[:200]}...")
    except Exception as e:
        print(f"❌ File extraction failed: {e}")
        return
    
    print("STEP 1: Extract LinkedIn data")
    try:
        linkedin_data = run_linkedin_extraction(linkedin_url)
        print(f"✅ LinkedIn extraction successful - {len(linkedin_data)} fields")
    except Exception as e:
        print(f"❌ LinkedIn extraction failed: {e}")
        return
        
    print("\nSTEP 2: Multi-source extraction with LinkedIn + Buyer Profile")
    try:
        extracted_data = extract_profile_from_multiple_sources(
            buyer_profile_text=buyer_profile_text,
            resume_text=None,
            linkedin_data=linkedin_data,
            agent_name='Profile Extraction Agent',
            user=None,
            session_id="debug_multi_test"
        )
        
        print(f"✅ Multi-source extraction completed")
        print(f"🏗️ Response type: {type(extracted_data)}")
        
        if isinstance(extracted_data, dict):
            # Check key fields
            print(f"\n📊 Key Fields:")
            key_fields = ['first_name', 'investment_experience', 'deal_size_preference', 'education', 'professional_experience']
            for field in key_fields:
                if field in extracted_data:
                    value = extracted_data[field]
                    if isinstance(value, dict) and 'value' in value:
                        print(f"   {field}: {value.get('confidence', 'unknown')} confidence - {str(value.get('value', 'None'))[:100]}...")
                    else:
                        print(f"   {field}: {str(value)[:100]}...")
                else:
                    print(f"   {field}: MISSING")
            
        else:
            print(f"❌ Unexpected response type: {type(extracted_data)}")
            print(f"Response: {extracted_data}")
            
    except Exception as e:
        print(f"❌ Multi-source extraction failed: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        
        # Try to identify if it's a JSON parsing error
        if "Unterminated string" in str(e) or "JSON" in str(e):
            print("\n🔍 JSON PARSING ERROR DETECTED")
            print("This likely means the AI returned malformed JSON with unescaped quotes or newlines.")
            print("Need to enhance JSON cleaning in the AI response handler.")
        
    print("\n" + "=" * 60)
    print("🏁 Multi-source test completed")

if __name__ == "__main__":
    test_multi_source_with_files()
