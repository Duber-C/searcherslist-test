#!/usr/bin/env python3

"""
Debug script to test multi-source extraction with LinkedIn data
This mimics exactly what the API endpoint does
"""

import sys
import os
sys.path.append('/Users/lbz/Documents/ShareHolder/searcherlist/searcher-backend')

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')
import django
django.setup()

def test_multi_source_extraction():
    from linkedIn_extraction import run_linkedin_extraction
    from ai_profile_creation.chatGpt import extract_profile_from_multiple_sources, format_linkedin_data_for_extraction
    import json

    linkedin_url = 'https://www.linkedin.com/in/luis-bernardo-zuluaga-gomez-859431218/'
    print("🧪 DEBUGGING MULTI-SOURCE EXTRACTION PIPELINE")
    print("=" * 60)
    
    # Step 1: Extract LinkedIn data (same as API)
    print("STEP 1: Extract LinkedIn data")
    try:
        linkedin_data = run_linkedin_extraction(linkedin_url)
        print(f"✅ LinkedIn extraction successful")
        print(f"🔢 Fields found: {len([k for k, v in linkedin_data.items() if v is not None and v != '' and v != []])}")
        
        # Show key fields
        if 'professional_experience' in linkedin_data:
            prof_exp = linkedin_data['professional_experience']
            print(f"📋 Professional experience: {type(prof_exp)} with {len(prof_exp) if isinstance(prof_exp, list) else 0} entries")
        if 'education' in linkedin_data:
            education = linkedin_data['education']
            print(f"🎓 Education: {type(education)} with {len(education) if isinstance(education, list) else 0} entries")
            
    except Exception as e:
        print(f"❌ LinkedIn extraction failed: {e}")
        return
        
    # Step 2: Format LinkedIn data for AI (same as API)
    print("\nSTEP 2: Format LinkedIn data for AI")
    linkedin_text = format_linkedin_data_for_extraction(linkedin_data)
    print(f"✅ LinkedIn text formatted ({len(linkedin_text)} characters)")
    print("📄 LinkedIn text preview:")
    print("-" * 40)
    print(linkedin_text[:800] + "..." if len(linkedin_text) > 800 else linkedin_text)
    print("-" * 40)
    
    # Step 3: Call multi-source extraction (same as API)
    print("\nSTEP 3: Call multi-source AI extraction")
    try:
        extracted_data = extract_profile_from_multiple_sources(
            buyer_profile_text=None,
            resume_text=None,
            linkedin_data=linkedin_data,
            agent_name='Profile Extraction Agent',
            user=None,
            session_id="debug_test"
        )
        
        print(f"✅ AI extraction completed")
        print(f"🏗️ Response type: {type(extracted_data)}")
        
        if isinstance(extracted_data, dict):
            # Check the problematic fields
            education = extracted_data.get('education')
            prof_exp = extracted_data.get('professional_experience')
            
            print(f"\n🎓 EDUCATION field:")
            print(f"   Type: {type(education)}")
            print(f"   Value: {education}")
            
            print(f"\n💼 PROFESSIONAL_EXPERIENCE field:")
            print(f"   Type: {type(prof_exp)}")
            print(f"   Value: {prof_exp}")
            
            # Show all fields with values
            populated_fields = [k for k, v in extracted_data.items() if v is not None and v != '' and v != [] and (not isinstance(v, dict) or v.get('value') is not None)]
            print(f"\n📊 Fields with data: {len(populated_fields)}")
            for field in populated_fields[:10]:  # Show first 10
                value = extracted_data[field]
                print(f"   {field}: {type(value)} = {str(value)[:100]}...")
            
        else:
            print(f"❌ Unexpected AI response type: {type(extracted_data)}")
            print(f"Response: {extracted_data}")
            
    except Exception as e:
        print(f"❌ AI extraction failed: {e}")
        import traceback
        traceback.print_exc()
        
    print("\n" + "=" * 60)
    print("🏁 Debug test completed")

if __name__ == "__main__":
    test_multi_source_extraction()
