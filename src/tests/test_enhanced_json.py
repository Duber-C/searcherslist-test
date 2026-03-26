#!/usr/bin/env python3

import os
import sys
import json
import tempfile

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Django setup
import django
from django.conf import settings
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')
    django.setup()

# Test the enhanced JSON parsing
def test_json_parsing():
    from ai_profile_creation.chatGpt import extract_profile_from_multiple_sources, extract_text_from_docx
    
    # Test with the problematic buyer profile file
    file_path = './ai_profile_creation/Grant Williams FINAL BUYER PROFILE - Cohort 59.docx'
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    try:
        print("🚀 Testing multi-source extraction with enhanced JSON parsing...")
        
        # Extract text from the file
        buyer_profile_text = extract_text_from_docx(file_path)
        print(f"📄 Extracted text length: {len(buyer_profile_text)} characters")
        
        # Test multi-source extraction
        result = extract_profile_from_multiple_sources(
            buyer_profile_text=buyer_profile_text,
            resume_text=None,
            linkedin_data=None,
            agent_name='Profile Extraction Agent',
            user=None,
            session_id='test_json_parsing'
        )
        
        print("✅ Multi-source extraction completed successfully!")
        print(f"📊 Result type: {type(result)}")
        print(f"📊 Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        # Check for specific fields
        test_fields = ['first_name', 'last_name', 'investment_experience', 'professional_experience']
        for field in test_fields:
            if field in result:
                value = result[field]
                print(f"  {field}: {type(value)} = {str(value)[:100]}...")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return None

if __name__ == "__main__":
    test_json_parsing()
