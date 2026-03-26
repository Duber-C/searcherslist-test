#!/usr/bin/env python3

import sys
import os

# Add the parent directory to the path to import Django models
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai_profile_creation'))

from chatGpt import format_linkedin_data_for_extraction

# Test with sample LinkedIn data in our schema format
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
    "geographic_focus": "Área metropolitana de Bogotá D.C.",
    "bio": "I'm a Product Designer with 12+ years of experience..."
}

print("=== TESTING LINKEDIN DATA FORMATTING ===")
print("\nOriginal LinkedIn data:")
print(sample_linkedin_data)

print("\n=== FORMATTED FOR AI EXTRACTION ===")
formatted_text = format_linkedin_data_for_extraction(sample_linkedin_data)
print(formatted_text)

print("\n=== CHECKING FOR FIRST/LAST NAME ===")
if "Morcio" in formatted_text and "Sierra" in formatted_text:
    print("✅ PASS: First and last names are present in formatted text")
else:
    print("❌ FAIL: First and last names missing from formatted text")
    print(f"Contains 'Morcio': {'Morcio' in formatted_text}")
    print(f"Contains 'Sierra': {'Sierra' in formatted_text}")