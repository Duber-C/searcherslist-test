#!/usr/bin/env python3

import os
import sys
import django

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'searcher_api.settings')
django.setup()

def test_multi_source_with_linkedin():
    """Test multi-source extraction with LinkedIn URL to trace data flow"""
    
    print("🧪 TESTING MULTI-SOURCE EXTRACTION WITH LINKEDIN")
    print("=" * 60)
    
    # Test data
    linkedin_url = "https://www.linkedin.com/in/luis-bernardo-zuluaga-gomez-859431218/"
    
    print(f"🔗 Testing with LinkedIn URL: {linkedin_url}")
    print()
    
    try:
        # Step 1: Test LinkedIn extraction directly
        print("📋 STEP 1: Testing LinkedIn extraction directly...")
        print("-" * 40)
        
        from linkedIn_extraction import run_linkedin_extraction
        linkedin_data = run_linkedin_extraction(linkedin_url)
        
        print("✅ LinkedIn extraction successful!")
        populated_fields = [k for k, v in linkedin_data.items() if v is not None and v != '' and v != []]
        print(f"📊 Populated fields ({len(populated_fields)}): {populated_fields}")
        
        # Show key fields
        print("\n🔑 Key LinkedIn fields:")
        key_fields = ['first_name', 'last_name', 'education', 'professional_experience', 'background']
        for field in key_fields:
            value = linkedin_data.get(field)
            if isinstance(value, list):
                print(f"  {field}: Array with {len(value)} items")
            elif value:
                print(f"  {field}: {str(value)[:100]}...")
            else:
                print(f"  {field}: None/Empty")
        
        print()
        
        # Step 2: Test multi-source AI extraction
        print("📋 STEP 2: Testing multi-source AI extraction...")
        print("-" * 40)
        
        from ai_profile_creation.chatGpt import extract_profile_from_multiple_sources
        
        # Simulate the exact call from views.py
        extracted_data = extract_profile_from_multiple_sources(
            buyer_profile_text=None,
            resume_text=None,
            linkedin_data=linkedin_data,
            agent_name='Profile Extraction Agent',
            user=None,
            session_id=f"test_multi_source_{hash(linkedin_url)}"
        )
        
        print("✅ Multi-source AI extraction completed!")
        print(f"📊 AI response type: {type(extracted_data)}")
        
        if isinstance(extracted_data, dict):
            ai_populated_fields = [k for k, v in extracted_data.items() if v is not None and v != '' and v != []]
            print(f"📊 AI populated fields ({len(ai_populated_fields)}): {ai_populated_fields}")
            
            # Compare LinkedIn input vs AI output
            print("\n🔄 LINKEDIN → AI FIELD MAPPING:")
            print("-" * 40)
            comparison_fields = ['first_name', 'last_name', 'education', 'professional_experience', 'background', 'current_role', 'company']
            
            for field in comparison_fields:
                linkedin_val = linkedin_data.get(field)
                ai_val = extracted_data.get(field)
                
                linkedin_has = bool(linkedin_val and linkedin_val != '' and linkedin_val != [])
                ai_has = bool(ai_val and ai_val != '' and ai_val != [])
                
                status = "✅" if (linkedin_has and ai_has) else "❌" if linkedin_has else "⚪"
                print(f"  {status} {field}: LinkedIn={linkedin_has} → AI={ai_has}")
            
            # Show full AI response
            print("\n📄 FULL AI RESPONSE:")
            print("-" * 40)
            import json
            print(json.dumps(extracted_data, indent=2, ensure_ascii=False))
            
        else:
            print(f"❌ Unexpected AI response: {extracted_data}")
        
        print()
        
        # Step 3: Show what would be sent to frontend
        print("📋 STEP 3: Frontend response simulation...")
        print("-" * 40)
        
        response_data = {
            'status': 'success',
            'message': 'Multi-source AI extraction completed using 1 sources',
            'extracted_data': extracted_data,
            'sources_processed': ['linkedin'],
            'sources_count': 1
        }
        
        print("📤 Response to frontend:")
        print(json.dumps(response_data, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_multi_source_with_linkedin()