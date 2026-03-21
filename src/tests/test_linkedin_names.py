#!/usr/bin/env python3

import sys
import os

# Add the parent directory to the path to import Django models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Django setup
import django
from django.conf import settings
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'searcher_api.settings')
    django.setup()

from ai_profile_creation.chatGpt import extract_profile_from_multiple_sources

# Test with LinkedIn data only (to isolate the issue)
sample_linkedin_data = {
    "first_name": "Morcio",
    "last_name": "Sierra", 
    "country": "Colombia",
    "city": "Bogota",
    "state": None,
    "linkedin_url": "https://www.linkedin.com/in/morcio",
    "background": "I'm a Product Designer with 12+ years of experience delivering impact across fintech, proptech, luxury, IoT, AR/VR, and emerging tech.",
    "current_role": "Lead UX/UI Designer",
    "company": "Kopius",
    "education": "Collège LaSalle, Montréal — Computer Graphics — Animation and Multimedia,  Graphic Design — 2010-01-01 to 2012-12-31",
    "languages": "English, Spanish, Italian",
    "geographic_focus": "Área metropolitana de Bogotá D.C."
}

print("=== TESTING MULTI-SOURCE EXTRACTION WITH LINKEDIN ONLY ===")
print("Testing if first_name and last_name are properly extracted from LinkedIn data...")

try:
    result = extract_profile_from_multiple_sources(
        buyer_profile_text=None,
        resume_text=None,
        linkedin_data=sample_linkedin_data,
        agent_name='Profile Extraction Agent'
    )
    
    print("\n=== EXTRACTION RESULTS ===")
    print(f"first_name: {result.get('first_name')}")
    print(f"last_name: {result.get('last_name')}")
    print(f"country: {result.get('country')}")
    print(f"current_role: {result.get('current_role')}")
    print(f"company: {result.get('company')}")
    
    # Check specifically for first and last name
    if result.get('first_name') == "Morcio" and result.get('last_name') == "Sierra":
        print("\n✅ SUCCESS: First and last names extracted correctly!")
    else:
        print(f"\n❌ ISSUE: Expected 'Morcio' and 'Sierra', got '{result.get('first_name')}' and '{result.get('last_name')}'")
        
    # Show full result for debugging
    print(f"\n=== FULL RESULT ===")
    import json
    print(json.dumps(result, indent=2))
        
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()