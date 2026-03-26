#!/usr/bin/env python3

import os
import sys
import django

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')
django.setup()

from linkedIn_extraction import run_linkedin_extraction

def test_linkedin_extraction():
    """Test LinkedIn extraction with specific profile"""
    
    linkedin_url = "https://www.linkedin.com/in/luis-bernardo-zuluaga-gomez-859431218/"
    print(f"🔍 Testing LinkedIn extraction with: {linkedin_url}")
    print("=" * 60)
    
    try:
        result = run_linkedin_extraction(linkedin_url)
        
        print("📋 EXTRACTION RESULTS:")
        print("=" * 60)
        
        # Check basic info
        print(f"Name: {result.get('first_name')} {result.get('last_name')}")
        print(f"Current Role: {result.get('current_role')}")
        print(f"Company: {result.get('company')}")
        print(f"Location: {result.get('geographic_focus')}")
        print(f"Industry: {result.get('industry_focus')}")
        
        print("\n🎓 EDUCATION:")
        print("-" * 30)
        education = result.get('education')
        if education:
            if isinstance(education, list):
                print(f"Education type: Array with {len(education)} entries")
                for i, edu in enumerate(education, 1):
                    print(f"  {i}. School: {edu.get('school', 'N/A')}")
                    print(f"     Degree: {edu.get('degree', 'N/A')}")
                    print(f"     Field: {edu.get('field', 'N/A')}")
                    print(f"     Years: {edu.get('years', 'N/A')}")
                    print()
            else:
                print(f"Education type: {type(education)}")
                print(f"Education value: {education}")
        else:
            print("❌ No education data found")
        
        print("\n💼 PROFESSIONAL EXPERIENCE:")
        print("-" * 30)
        prof_exp = result.get('professional_experience')
        if prof_exp:
            if isinstance(prof_exp, list):
                print(f"Experience type: Array with {len(prof_exp)} entries")
                for i, exp in enumerate(prof_exp, 1):
                    print(f"  {i}. Company: {exp.get('company', 'N/A')}")
                    print(f"     Title: {exp.get('title', 'N/A')}")
                    print(f"     Duration: {exp.get('duration', 'N/A')}")
                    print(f"     Description: {exp.get('description', 'N/A')[:100]}..." if exp.get('description') else "     Description: N/A")
                    print()
            else:
                print(f"Experience type: {type(prof_exp)}")
                print(f"Experience value: {prof_exp}")
        else:
            print("❌ No professional experience data found")
        
        print("\n🔧 OTHER FIELDS:")
        print("-" * 30)
        print(f"Background: {result.get('background', 'N/A')[:100]}..." if result.get('background') else "Background: N/A")
        print(f"Bio: {result.get('bio', 'N/A')[:100]}..." if result.get('bio') else "Bio: N/A")
        print(f"Skills: {result.get('skills', 'N/A')[:100]}..." if result.get('skills') else "Skills: N/A")
        print(f"Languages: {result.get('languages', 'N/A')}")
        
        print("\n📊 FULL RAW DATA:")
        print("=" * 60)
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ Error during extraction: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_linkedin_extraction()
