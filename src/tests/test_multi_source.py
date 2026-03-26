#!/usr/bin/env python3
"""
Test script for multi-source profile extraction
Demonstrates the new buyer profile priority system
"""

import os
import sys
import django

# Setup Django
sys.path.append('/Users/lbz/Documents/ShareHolder/searcherlist/searcher-backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')
django.setup()

from users.models import User
from ai_profile_creation.chatGpt import extract_profile_from_multiple_sources

def test_multi_source_extraction():
    """Test multi-source extraction with sample data"""
    
    # Sample buyer profile (TOP PRIORITY)
    buyer_profile_text = """
    BUYER PROFILE - John Smith
    
    TARGET BUSINESS CRITERIA:
    - Industry Focus: Software-as-a-Service (SaaS), E-commerce platforms
    - Revenue Range: $2M - $10M annually
    - Geographic Focus: West Coast USA
    - Deal Size: $5M - $25M enterprise value
    - Investment Experience: 8 years private equity, 3 acquisitions completed
    
    BACKGROUND:
    Experienced investor with focus on tech-enabled services. Currently Managing Director at Growth Capital Partners.
    """
    
    # Sample resume (HIGH PRIORITY for experience details)
    resume_text = """
    JOHN SMITH
    Senior Investment Manager
    
    EXPERIENCE:
    • Managing Director, Growth Capital Partners (2019-Present)
      - Led 15+ acquisition deals totaling $150M in transaction value
      - Specialized in SaaS and marketplace businesses
      - Managed portfolio of 8 companies
    
    • Senior Associate, Tech Ventures (2016-2019)
      - Conducted due diligence on 50+ investment opportunities
      - Focus on B2B software and e-commerce
    
    EDUCATION:
    • MBA, Stanford Graduate School of Business (2016) - Finance & Strategy
    • BS Computer Science, UC Berkeley (2012) - Magna Cum Laude
    
    SKILLS: Financial modeling, due diligence, portfolio management, strategic planning
    """
    
    # Sample LinkedIn data (MEDIUM PRIORITY for current info)
    linkedin_data = {
        "name": "John Smith",
        "headline": "Managing Director at Growth Capital Partners | SaaS & E-commerce Investor",
        "location": "San Francisco, CA",
        "summary": "Passionate about helping entrepreneurs scale their businesses through strategic capital and operational expertise.",
        "experience": [
            {
                "title": "Managing Director",
                "company": "Growth Capital Partners",
                "duration": "2019 - Present",
                "description": "Leading investment activities in B2B software sector"
            }
        ],
        "education": [
            {
                "school": "Stanford Graduate School of Business",
                "degree": "Master of Business Administration",
                "field": "Finance & Strategy",
                "years": "2014-2016"
            }
        ],
        "skills": ["Private Equity", "Due Diligence", "Portfolio Management", "SaaS", "E-commerce"]
    }
    
    print("🚀 Testing Multi-Source Profile Extraction")
    print("=" * 50)
    print(f"📊 Sources: Buyer Profile ({len(buyer_profile_text)} chars), Resume ({len(resume_text)} chars), LinkedIn (structured)")
    print()
    
    try:
        # Extract using multi-source with buyer profile priority
        result = extract_profile_from_multiple_sources(
            buyer_profile_text=buyer_profile_text,
            resume_text=resume_text,
            linkedin_data=linkedin_data,
            agent_name='Profile Extraction Agent',
            session_id='test_multi_source'
        )
        
        print("✅ Extraction completed successfully!")
        print()
        
        # Show priority-based results
        priority_fields = {
            "Investment Focus (Buyer Profile Priority)": [
                'investment_experience', 'deal_size_preference', 
                'industry_focus', 'geographic_focus'
            ],
            "Experience Details (Resume Priority)": [
                'background', 'achievements', 'education', 'professional_experience', 'years_experience'
            ],
            "Current Info (LinkedIn Priority)": [
                'first_name', 'last_name', 'current_role', 'company'
            ]
        }
        
        for category, fields in priority_fields.items():
            print(f"📋 {category}:")
            for field in fields:
                if field in result:
                    value = result[field].get('value', 'N/A')
                    confidence = result[field].get('confidence', 'unknown')
                    print(f"  • {field}: {confidence} confidence")
                    
                    # Special handling for structured fields
                    if field in ['education', 'professional_experience'] and isinstance(value, list):
                        print(f"    [{len(value)} entries]")
                        for i, item in enumerate(value[:2]):  # Show first 2 entries
                            if isinstance(item, dict):
                                if field == 'education':
                                    school = item.get('school', 'Unknown School')
                                    degree = item.get('degree', 'Unknown Degree')
                                    years = item.get('years', '')
                                    print(f"      {i+1}. {degree} - {school} {f'({years})' if years else ''}")
                                elif field == 'professional_experience':
                                    title = item.get('title', 'Unknown Title')
                                    company = item.get('company', 'Unknown Company')
                                    duration = item.get('duration', '')
                                    print(f"      {i+1}. {title} at {company} {f'({duration})' if duration else ''}")
                        if len(value) > 2:
                            print(f"      ... and {len(value)-2} more entries")
                    elif value and len(str(value)) > 100:
                        print(f"    {str(value)[:100]}...")
                    else:
                        print(f"    {value}")
            print()
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_multi_source_extraction()
