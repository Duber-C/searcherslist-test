#!/usr/bin/env python3

"""
Debug script to capture and analyze the malformed JSON response
"""

import sys
import os
sys.path.append('/Users/lbz/Documents/ShareHolder/searcherlist/searcher-backend')

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')
import django
django.setup()

def debug_ai_response():
    from linkedIn_extraction import run_linkedin_extraction
    from ai_profile_creation.chatGpt import extract_text_from_docx
    from users.models import AIAgent, AIInteractionLog
    from ai_profile_creation.chatGpt import get_ai_client
    import json

    print("🔍 DEBUGGING AI JSON RESPONSE")
    print("=" * 60)
    
    # Get the same data
    linkedin_url = 'https://www.linkedin.com/in/grant-nelson-williams/'
    grant_williams_file = "/Users/lbz/Documents/ShareHolder/searcherlist/searcher-backend/ai_profile_creation/Grant Williams FINAL BUYER PROFILE - Cohort 59.docx"
    
    print("📊 Extracting data...")
    linkedin_data = run_linkedin_extraction(linkedin_url)
    buyer_profile_text = extract_text_from_docx(grant_williams_file)
    
    # Manually build the prompt (same as multi-source function)
    from ai_profile_creation.chatGpt import format_linkedin_data_for_extraction, EXTRACTION_SCHEMA
    
    sources = []
    source_priorities = []
    
    sources.append(f"BUYER PROFILE (HIGHEST PRIORITY - Use for investment criteria, deal preferences, business focus):\n{buyer_profile_text}")
    source_priorities.append("Buyer Profile: TOP priority for investment_experience, deal_size_preference, industry_focus, geographic_focus, value_proposition")
    
    linkedin_text = format_linkedin_data_for_extraction(linkedin_data)
    sources.append(f"LINKEDIN PROFILE (MEDIUM PRIORITY - Use for current professional info, basic details):\n{linkedin_text}")
    source_priorities.append("LinkedIn: Medium priority for first_name, last_name, current_role, company, linkedin_url, basic professional info")
    
    multi_source_text = f"""
MULTI-SOURCE PROFILE EXTRACTION
=================================

PRIORITY INSTRUCTIONS:
{chr(10).join(source_priorities)}

FIELD PRIORITY RULES:
- Investment/Business Focus: Buyer Profile > Resume > LinkedIn
- Personal Info: LinkedIn > Resume > Buyer Profile  
- Detailed Experience: Resume > Buyer Profile > LinkedIn
- Current Professional: LinkedIn > Resume > Buyer Profile

AVAILABLE SOURCES:
{chr(10).join(sources)}

EXTRACTION RULES:
1. Use the HIGHEST PRIORITY source available for each field
2. If a field is missing from the highest priority source, check the next priority source
3. When multiple sources have the same info, prefer the higher priority source
4. Set confidence as 'high' when data comes from appropriate priority source
5. Set confidence as 'medium' when using secondary source
6. Set confidence as 'low' when data is unclear or missing from all sources
7. PRESERVE ALL ENTRIES for arrays (education, professional_experience) - do NOT summarize or condense multiple entries into one
8. For professional_experience array, include EVERY job entry with full details (company, title, duration, description, achievements)

REQUIRED OUTPUT SCHEMA (use these exact field names):
{json.dumps(EXTRACTION_SCHEMA, indent=2)}

Extract comprehensive profile information following the schema and priority rules above.
Use the EXACT field names from the schema - do not use variations like 'full_name', 'phone', 'email', etc.
"""
    
    print(f"📝 Input prompt length: {len(multi_source_text)} characters")
    
    # Get AI agent
    agent = AIAgent.objects.get(name='Profile Extraction Agent', agent_type='profile_extraction', is_active=True)
    client = get_ai_client(agent.ai_service)
    
    # Enhanced system prompt for clean JSON output
    enhanced_system_prompt = f"""{agent.system_prompt}

CRITICAL JSON OUTPUT REQUIREMENTS:
1. Return ONLY valid JSON - absolutely NO markdown, code blocks, explanations, or extra text
2. ALL strings must be properly escaped - use backslash escaping for special characters
3. Use null (not empty strings) for missing/unknown values
4. Validate JSON syntax - ensure all brackets, braces, and quotes are properly closed
5. Keep string values concise - break long text into multiple sentences with proper escaping
6. If content contains problematic characters, summarize instead of including verbatim
7. Test your JSON output mentally before responding
8. IMPORTANT: If any field contains quotes, newlines, or special characters, properly escape them with backslashes

FAILURE TO FOLLOW THESE RULES WILL CAUSE SYSTEM ERRORS.
"""
    
    print("🤖 Calling AI...")
    response = client.chat.completions.create(
        model=agent.ai_service.model_name,
        messages=[
            {"role": "system", "content": enhanced_system_prompt},
            {"role": "user", "content": multi_source_text + "\n\nRespond with valid JSON only - no markdown or code blocks."}
        ],
        temperature=0.7,
        max_tokens=2000
    )
    
    response_text = response.choices[0].message.content
    
    print(f"📄 AI response length: {len(response_text)} characters")
    print("🔍 AI response (showing problem area around char 8300-8400):")
    start_char = max(0, 8300 - 100)
    end_char = min(len(response_text), 8400 + 100)
    print(f"Characters {start_char}-{end_char}:")
    print("'" + response_text[start_char:end_char] + "'")
    
    # Try to find the exact problem
    print("\n🔍 Analyzing JSON structure...")
    try:
        json.loads(response_text)
        print("✅ JSON is actually valid!")
    except json.JSONDecodeError as e:
        print(f"❌ JSON error: {e}")
        print(f"Error position: line {e.lineno}, column {e.colno}, character {e.pos}")
        
        # Show context around the error
        if e.pos < len(response_text):
            start = max(0, e.pos - 50)
            end = min(len(response_text), e.pos + 50)
            print(f"Context around error (chars {start}-{end}):")
            problem_text = response_text[start:end]
            print("'" + problem_text + "'")
            
            # Highlight the exact problem character
            error_char = e.pos - start
            if 0 <= error_char < len(problem_text):
                print(" " * error_char + "^")
                print(f"Problem character: '{problem_text[error_char]}' (ASCII: {ord(problem_text[error_char])})")
    
    print("=" * 60)
    print("🏁 Debug completed")

if __name__ == "__main__":
    debug_ai_response()
