import os
import json
import sys
from docx import Document
from decimal import Decimal

# Add the parent directory to the path to import Django models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Django setup
import django
from django.conf import settings
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'searcher_api.settings')
    django.setup()

from users.models import AIService, AIAgent, AIInteractionLog

# -----------------------------------------------------------
# 2. Extract text from DOCX
# -----------------------------------------------------------

def extract_text_from_docx(path):
    doc = Document(path)
    return "\n".join([p.text for p in doc.paragraphs])

# -----------------------------------------------------------
# 3. AI Service Client Factory
# -----------------------------------------------------------

def get_ai_client(ai_service):
    """Get the appropriate AI client based on the service type"""
    if ai_service.service_type == 'openai':
        from openai import OpenAI
        from django.conf import settings
        
        # Get API key from Django settings
        api_key = getattr(settings, ai_service.api_key_name, None)
        
        if not api_key:
            raise ValueError(f"API key not found in Django settings: {ai_service.api_key_name}")
        return OpenAI(api_key=api_key)
    elif ai_service.service_type == 'azure':
        from openai import AzureOpenAI
        from django.conf import settings
        
        # Get API key from Django settings
        api_key = getattr(settings, ai_service.api_key_name, None)
        endpoint = ai_service.api_endpoint
        if not api_key or not endpoint:
            raise ValueError("Azure OpenAI requires both API key and endpoint")
        return AzureOpenAI(api_key=api_key, azure_endpoint=endpoint)
    else:
        raise NotImplementedError(f"AI service type '{ai_service.service_type}' not implemented yet")


# -----------------------------------------------------------
# 3. GPT extraction
# -----------------------------------------------------------

EXTRACTION_SCHEMA = {
    "first_name": "string or null",
    "last_name": "string or null",
    "phone_number": "string or null",
    "country": "string or null",
    "city": "string or null",
    "state": "string or null",
    "linkedin_url": "string or null",
    "background": "short summary or null",
    "acquisition_target": "short summary of what the user is looking to buy or null (explicit buyer profile content should populate this)",
    "value_proposition": "short summary or null",
    "areas_of_expertise": "bullet list or null",
    "investment_experience": "string or null",
    "deal_size_preference": "string or null",
    "industry_focus": "summary or null",
    "geographic_focus": "string or null",
    "current_role": "string or null",
    "company": "string or null",
    "years_experience": "string or null",
    "education": "array of objects [{school: string, degree: string, field: string, years: string, description: string}, ...] or null - ALL fields must be strings, use 'Unknown' for missing values, never null",
    "professional_experience": "array of objects [{company: string, title: string, duration: string, description: string, achievements: string}, ...] or null - ALL fields must be strings, use 'Unknown' for missing values, never null",
    "certifications": "summary or null",
    "achievements": "summary or null",
    "website": "string or null",
    "bio": "summary or null",
    "skills": "summary or null",
    "languages": "string or null"
}

def extract_profile_from_text(text, agent_name='Profile Extraction Agent', user=None, session_id=None):
    """
    Extract profile information using AI models from database (single source)
    
    Args:
        text: The input text to process
        agent_name: Name of the AI agent to use (defaults to 'Profile Extraction Agent')
        user: User model instance (optional, for logging)
        session_id: Session identifier (optional, for logging)
    
    Returns:
        dict: Extracted profile data
    """
    from django.utils import timezone
    
    # Get the AI agent from database
    try:
        agent = AIAgent.objects.get(name=agent_name, agent_type='profile_extraction', is_active=True)
    except AIAgent.DoesNotExist:
        # Fallback to default agent if specified one doesn't exist
        try:
            agent = AIAgent.objects.filter(agent_type='profile_extraction', is_active=True).first()
            if not agent:
                raise ValueError("No active profile extraction agent found in database")
        except Exception as e:
            raise ValueError(f"No profile extraction agent found: {str(e)}")
    
    # Create interaction log
    log = AIInteractionLog.objects.create(
        agent=agent,
        user=user,
        session_id=session_id or '',
        input_text=text,
        system_prompt_used=agent.system_prompt,
        user_prompt_used=agent.user_prompt_template.format(
            text=text,
            schema=json.dumps(EXTRACTION_SCHEMA, indent=2)
        ),
        temperature_used=agent.get_effective_temperature(),
        max_tokens_used=agent.get_effective_max_tokens(),
        model_used=agent.ai_service.model_name,
    )
    
    try:
        # Get AI client
        client = get_ai_client(agent.ai_service)
        
        # Prepare messages
        messages = []
        if agent.system_prompt.strip():
            messages.append({"role": "system", "content": agent.system_prompt})
        
        user_prompt = agent.user_prompt_template.format(
            text=text,
            schema=json.dumps(EXTRACTION_SCHEMA, indent=2)
        )
        messages.append({"role": "user", "content": user_prompt})
        
        # Enhance the user prompt with JSON output instructions
        if messages and messages[-1]["role"] == "user":
            messages[-1]["content"] += "\n\nRespond with valid JSON only - no markdown or code blocks."
        
        # Make API call
        print("🤖 SENDING TO OPENAI API:")
        print("=" * 60)
        print(f"Model: {agent.ai_service.model_name}")
        print(f"Temperature: {agent.get_effective_temperature()}")
        print(f"Max tokens: {agent.get_effective_max_tokens()}")
        print("Messages being sent:")
        for i, msg in enumerate(messages):
            content_preview = msg["content"][:300] + "..." if len(msg["content"]) > 300 else msg["content"]
            print(f"  {i+1}. {msg['role']}: {content_preview}")
        print("=" * 60)
        
        response = client.chat.completions.create(
            model=agent.ai_service.model_name,
            temperature=agent.get_effective_temperature(),
            max_tokens=agent.get_effective_max_tokens(),
            messages=messages
        )
        
        print("🤖 OPENAI API RESPONSE:")
        print("=" * 60)
        print(f"Response model: {response.model}")
        print(f"Usage: {response.usage}")
        response_content = response.choices[0].message.content
        print(f"Response content (first 500 chars): {response_content[:500]}...")
        print("=" * 60)
        
        # Extract response
        raw_content = response.choices[0].message.content
        
        # Clean and validate JSON response
        try:
            parsed_data = json.loads(raw_content)
        except json.JSONDecodeError as json_error:
            print(f"JSON Decode Error: {str(json_error)}")
            print(f"Raw response content: {raw_content[:1000]}...")
            
            # Advanced JSON cleaning
            cleaned_content = raw_content.strip()
            
            # Remove markdown code blocks if present
            if cleaned_content.startswith('```json'):
                cleaned_content = cleaned_content.replace('```json', '').replace('```', '').strip()
            elif cleaned_content.startswith('```'):
                cleaned_content = cleaned_content.replace('```', '').strip()
            
            # Fix common JSON issues
            import re
            
            # Fix unescaped quotes in strings
            def fix_unescaped_quotes(text):
                # Find all string values and fix unescaped quotes
                def replace_quotes(match):
                    string_content = match.group(1)
                    # Escape any unescaped quotes
                    string_content = string_content.replace('\\"', '___ESCAPED_QUOTE___')
                    string_content = string_content.replace('"', '\\"')
                    string_content = string_content.replace('___ESCAPED_QUOTE___', '\\"')
                    return f'"{string_content}"'
                
                # Pattern to match string values in JSON
                pattern = r'"([^"\\]*(\\.[^"\\]*)*)"'
                return re.sub(pattern, replace_quotes, text)
            
            # Fix newlines in strings
            def fix_newlines(text):
                # Replace unescaped newlines in string values
                def replace_newlines(match):
                    string_content = match.group(1)
                    string_content = string_content.replace('\n', '\\n')
                    string_content = string_content.replace('\r', '\\r')
                    string_content = string_content.replace('\t', '\\t')
                    return f'"{string_content}"'
                
                pattern = r'"([^"]*?)"'
                return re.sub(pattern, replace_newlines, text)
            
            # Try multiple cleaning strategies
            cleaning_attempts = [
                cleaned_content,  # Original cleaned
                fix_unescaped_quotes(cleaned_content),  # Fix quotes
                fix_newlines(cleaned_content),  # Fix newlines
                fix_newlines(fix_unescaped_quotes(cleaned_content))  # Both fixes
            ]
            
            parsed_data = None
            for i, attempt in enumerate(cleaning_attempts):
                try:
                    parsed_data = json.loads(attempt)
                    print(f"Successfully parsed JSON with cleaning strategy {i+1}")
                    break
                except json.JSONDecodeError as attempt_error:
                    print(f"Cleaning strategy {i+1} failed: {str(attempt_error)}")
                    continue
            
            if parsed_data is None:
                # Final fallback: try to extract JSON object manually
                try:
                    # Find the first { and last } to extract JSON object
                    start_idx = cleaned_content.find('{')
                    end_idx = cleaned_content.rfind('}')
                    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                        json_part = cleaned_content[start_idx:end_idx+1]
                        parsed_data = json.loads(json_part)
                        print("Successfully extracted and parsed JSON object")
                    else:
                        raise ValueError("Could not find valid JSON object boundaries")
                except (json.JSONDecodeError, ValueError) as final_error:
                    print(f"Final JSON extraction failed: {str(final_error)}")
                    raise ValueError(f"AI returned invalid JSON after all cleaning attempts. Original error: {str(json_error)}. Raw content preview: {raw_content[:200]}...")
                    # Escape any unescaped quotes
                    string_content = string_content.replace('\\"', '___ESCAPED_QUOTE___')
                    string_content = string_content.replace('"', '\\"')
                    string_content = string_content.replace('___ESCAPED_QUOTE___', '\\"')
                    return f'"{string_content}"'
                
                # Pattern to match string values in JSON
                pattern = r'"([^"\\]*(\\.[^"\\]*)*)"'
                return re.sub(pattern, replace_quotes, text)
            
            # Fix newlines in strings
            def fix_newlines(text):
                # Replace unescaped newlines in string values
                def replace_newlines(match):
                    string_content = match.group(1)
                    string_content = string_content.replace('\n', '\\n')
                    string_content = string_content.replace('\r', '\\r')
                    string_content = string_content.replace('\t', '\\t')
                    return f'"{string_content}"'
                
                pattern = r'"([^"]*?)"'
                return re.sub(pattern, replace_newlines, text)
            
            # Try multiple cleaning strategies
            cleaning_attempts = [
                cleaned_content,  # Original cleaned
                fix_unescaped_quotes(cleaned_content),  # Fix quotes
                fix_newlines(cleaned_content),  # Fix newlines
                fix_newlines(fix_unescaped_quotes(cleaned_content))  # Both fixes
            ]
            
            parsed_data = None
            for i, attempt in enumerate(cleaning_attempts):
                try:
                    parsed_data = json.loads(attempt)
                    print(f"Successfully parsed JSON with cleaning strategy {i+1}")
                    break
                except json.JSONDecodeError as attempt_error:
                    print(f"Cleaning strategy {i+1} failed: {str(attempt_error)}")
                    continue
            
            if parsed_data is None:
                # Final fallback: try to extract JSON object manually
                try:
                    # Find the first { and last } to extract JSON object
                    start_idx = cleaned_content.find('{')
                    end_idx = cleaned_content.rfind('}')
                    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                        json_part = cleaned_content[start_idx:end_idx+1]
                        parsed_data = json.loads(json_part)
                        print("Successfully extracted and parsed JSON object")
                    else:
                        raise ValueError("Could not find valid JSON object boundaries")
                except (json.JSONDecodeError, ValueError) as final_error:
                    print(f"Final JSON extraction failed: {str(final_error)}")
                    raise ValueError(f"AI returned invalid JSON after all cleaning attempts. Original error: {str(json_error)}. Raw content preview: {raw_content[:200]}...")
        
        # Log successful completion
        token_usage = {
            'prompt_tokens': response.usage.prompt_tokens,
            'completion_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens,
        }
        
        log.mark_completed(
            response_text=raw_content,
            parsed_response=parsed_data,
            token_usage=token_usage
        )
        
        return parsed_data
        
    except Exception as e:
        # Log error
        log.mark_completed(
            response_text='',
            error=e
        )
        raise e


def extract_profile_from_multiple_sources(buyer_profile_text=None, resume_text=None, linkedin_data=None, 
                                        questionnaire_answers=None, agent_name='Profile Extraction Agent', user=None, session_id=None):
    """
    Extract profile information from multiple sources with buyer profile priority
    
    Priority Order:
    1. Buyer Profile (TOP PRIORITY) - Investment criteria, deal preferences
    2. Resume - Detailed experience, achievements, education  
    3. LinkedIn - Current professional info, basic details
    4. Questionnaire - Answers to specific buyer profile questions
    
    Args:
        buyer_profile_text: Text from buyer profile document
        resume_text: Text from resume/CV document
        linkedin_data: Structured LinkedIn profile data
        questionnaire_answers: Dictionary of questionnaire answers
        agent_name: Name of the AI agent to use
        user: User model instance (optional, for logging)
        session_id: Session identifier (optional, for logging)
    
    Returns:
        dict: Extracted profile data with confidence scores
    """
    from django.utils import timezone
    
    # Build contextual prompt with all available sources
    sources = []
    source_priorities = []
    
    if buyer_profile_text:
        sources.append(f"BUYER PROFILE (HIGHEST PRIORITY - Use for investment criteria, deal preferences, business focus):\n{buyer_profile_text}")
        source_priorities.append("Buyer Profile: TOP priority for acquisition_target, investment_experience, deal_size_preference, industry_focus, geographic_focus, value_proposition")
    
    if resume_text:
        sources.append(f"RESUME/CV (HIGH PRIORITY - Use for detailed experience, achievements, education):\n{resume_text}")
        source_priorities.append("Resume: High priority for background, achievements, education, certifications, years_experience, areas_of_expertise")
    
    if linkedin_data:
        # Convert LinkedIn data to text format
        linkedin_text = format_linkedin_data_for_extraction(linkedin_data)
        sources.append(f"LINKEDIN PROFILE (MEDIUM PRIORITY - Use for current professional info, basic details):\n{linkedin_text}")
        source_priorities.append("LinkedIn: Medium priority for first_name, last_name, current_role, company, linkedin_url, basic professional info")
    
    if questionnaire_answers:
        # Format questionnaire answers for extraction
        questionnaire_text = "QUESTIONNAIRE ANSWERS (HIGH PRIORITY - Use for buyer-specific search criteria and preferences):\n"
        import json
        for question_id, answer in questionnaire_answers.items():
            formatted_answer = None
            if isinstance(answer, list):
                parts = []
                for item in answer:
                    if isinstance(item, dict):
                        # For AI input, prefer concise title/value only (omit subtitle)
                        title = item.get('title') or item.get('label') or item.get('value')
                        parts.append(f"{title}")
                    else:
                        parts.append(str(item))
                formatted_answer = ', '.join(parts)
            elif isinstance(answer, dict):
                # For AI input, send concise title/value only (do not include subtitle)
                title = answer.get('title') or answer.get('label') or answer.get('value')
                formatted_answer = f"{title}"
            else:
                try:
                    formatted_answer = str(answer)
                except Exception:
                    formatted_answer = json.dumps(answer)

            if formatted_answer and formatted_answer.strip():
                # Convert question IDs to readable format
                question_map = {
                    'target_business_types': 'Target Business Types',
                    'target_geography': 'Target Geography',
                    'size_metric': 'Size Metric Preference',
                    'size_range_min': 'Minimum Target Size',
                    'size_range_max': 'Maximum Target Size',
                    'other_search_notes': 'Additional Search Criteria',
                    'industry_geo_experience': 'Industry/Geographic Experience',
                    'owned_or_sold_before': 'Previous Business Ownership',
                    'three_five_words': 'Descriptive Words',
                    'enjoy_work_most': 'Preferred Work Type',
                    'pnl_experience': 'P&L Experience',
                    'customer_experience': 'Customer Service Experience',
                    'people_management': 'People Management Experience',
                    'entrepreneurial_experience': 'Entrepreneurial Experience',
                    'values_leadership_philosophy': 'Values and Leadership Philosophy',
                    'personal_interests': 'Personal Interests',
                    'why_buy': 'Why Buy a Business',
                    'well_suited': 'Why Well-Suited to be Owner'
                }
                question_label = question_map.get(question_id, question_id.replace('_', ' ').title())
                questionnaire_text += f"- {question_label}: {formatted_answer}\n"
        
        sources.append(questionnaire_text)
        source_priorities.append("Questionnaire: High priority for investment_experience, deal_size_preference, industry_focus, geographic_focus, value_proposition, areas_of_expertise, target search criteria")
    
    if not sources:
        raise ValueError("At least one data source must be provided")
    
    # Create comprehensive extraction prompt
    multi_source_text = f"""
MULTI-SOURCE PROFILE EXTRACTION
=================================

PRIORITY INSTRUCTIONS:
{chr(10).join(source_priorities)}

FIELD PRIORITY RULES:
- Investment/Business Focus: Buyer Profile > Questionnaire > Resume > LinkedIn
- Personal Info: LinkedIn > Resume > Questionnaire > Buyer Profile  
- Detailed Experience: Resume > Buyer Profile > LinkedIn > Questionnaire
- Current Professional: LinkedIn > Resume > Buyer Profile > Questionnaire
- Search Criteria & Preferences: Questionnaire > Buyer Profile > Resume > LinkedIn
- Education & Professional Experience: LinkedIn > Resume > Buyer Profile (IGNORE questionnaire for these fields)
- Certifications & Skills: Resume > LinkedIn > Buyer Profile > Questionnaire

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
9. CRITICAL: For education and professional_experience arrays, ONLY use LinkedIn and Resume data - IGNORE questionnaire completely for these fields
10. NEVER leave education or professional_experience as null if LinkedIn or Resume contains this information
11. RESPONSE FORMAT MUST BE IDENTICAL regardless of whether questionnaire data is present or not
12. Questionnaire is supplementary data only - do not change output schema or field types based on its presence
13. FIELD VALUE REQUIREMENTS:
    - education.degree: Use actual degree abbreviation (BS, MS, MBA, PhD) or program name, never null
    - education.field: Major/specialization field, use 'General' if unknown, never null  
    - education.years: Format as 'YYYY-YYYY' or 'Graduated YYYY', never null
    - education.description: Additional details or 'None', never null
    - professional_experience.title: Full job title, never null
    - professional_experience.duration: Format as 'YYYY-YYYY' or 'X years', never null
    - ALL string fields must be actual strings, use 'Unknown' instead of null values

REQUIRED OUTPUT SCHEMA (use these exact field names):
{json.dumps(EXTRACTION_SCHEMA, indent=2)}

Extract comprehensive profile information following the schema and priority rules above.
Use the EXACT field names from the schema - do not use variations like 'full_name', 'phone', 'email', etc.
"""
    
    # Get the AI agent from database
    try:
        agent = AIAgent.objects.get(name=agent_name, agent_type='profile_extraction', is_active=True)
    except AIAgent.DoesNotExist:
        try:
            agent = AIAgent.objects.filter(agent_type='profile_extraction', is_active=True).first()
            if not agent:
                raise ValueError("No active profile extraction agent found in database")
        except Exception as e:
            raise ValueError(f"No profile extraction agent found: {str(e)}")
    
    # Create interaction log
    log = AIInteractionLog.objects.create(
        agent=agent,
        user=user,
        session_id=session_id or '',
        input_text=multi_source_text,
        temperature_used=agent.custom_temperature or 0.7,
        max_tokens_used=agent.custom_max_tokens or 2000
    )
    
    try:
        # Get AI client and make request
        client = get_ai_client(agent.ai_service)
        
        # Get temperature and max_tokens from agent or service defaults
        # Use higher token limit for multi-source extraction due to larger response size
        temperature = agent.custom_temperature or 0.7
        max_tokens = agent.custom_max_tokens or 4000  # Increased from 2000 to handle complex multi-source responses
        
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

FAILURE TO FOLLOW THESE RULES WILL CAUSE SYSTEM ERRORS.
"""
        
        print("🚀 MULTI-SOURCE: SENDING TO OPENAI API:")
        print("=" * 70)
        print(f"Model: {agent.ai_service.model_name}")
        print(f"Temperature: {temperature}")
        print(f"Max tokens: {max_tokens}")
        print("System prompt length:", len(enhanced_system_prompt))
        full_user_content = multi_source_text + "\n\nRespond with valid JSON only - no markdown or code blocks."
        print("User prompt preview (first 800 chars):")
        print(full_user_content[:800] + "..." if len(full_user_content) > 800 else full_user_content)
        print("=" * 70)
        
        response = client.chat.completions.create(
            model=agent.ai_service.model_name,
            messages=[
                {"role": "system", "content": enhanced_system_prompt},
                {"role": "user", "content": full_user_content}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        print("🚀 MULTI-SOURCE: OPENAI API RESPONSE:")
        print("=" * 70)
        print(f"Response model: {response.model}")
        print(f"Usage: {response.usage}")
        response_content = response.choices[0].message.content
        print(f"Response length: {len(response_content)} characters")
        print("Response preview (first 600 chars):")
        print(response_content[:600] + "..." if len(response_content) > 600 else response_content)
        print("=" * 70)
        
        response_text = response.choices[0].message.content
        
        # Calculate costs
        input_tokens = response.usage.prompt_tokens if hasattr(response, 'usage') else 0
        output_tokens = response.usage.completion_tokens if hasattr(response, 'usage') else 0
        
        # Parse and validate response with robust error handling
        try:
            parsed_data = json.loads(response_text)
        except json.JSONDecodeError as json_error:
            print(f"Initial JSON parsing failed: {str(json_error)}")
            print(f"Raw AI response length: {len(response_text)}")
            print(f"Raw AI response preview: {response_text[:500]}...")
            
            # Apply comprehensive JSON cleaning
            raw_content = response_text
            cleaned_content = raw_content.strip()
            
            # Remove any markdown code blocks
            if '```json' in cleaned_content:
                cleaned_content = cleaned_content.split('```json')[1].split('```')[0].strip()
            elif '```' in cleaned_content:
                cleaned_content = cleaned_content.split('```')[1].split('```')[0].strip()
            
            # Helper functions for JSON cleaning
            def fix_unescaped_quotes(text):
                import re
                # Fix unescaped quotes within string values
                def replace_quotes(match):
                    string_content = match.group(1)
                    # Replace unescaped quotes with escaped quotes
                    fixed_content = string_content.replace('"', '\\"')
                    return f'"{fixed_content}"'
                
                pattern = r'"([^"]*?(?:[^\\"]"[^"]*?)*)"'
                return re.sub(pattern, replace_quotes, text)
            
            def fix_newlines(text):
                import re
                # Fix unescaped newlines within string values
                def replace_newlines(match):
                    string_content = match.group(1)
                    # Replace actual newlines with \\n
                    fixed_content = string_content.replace('\n', '\\n').replace('\r', '\\r')
                    return f'"{fixed_content}"'
                
                pattern = r'"([^"]*?)"'
                return re.sub(pattern, replace_newlines, text)
            
            # Try multiple cleaning strategies
            cleaning_attempts = [
                cleaned_content,  # Original cleaned
                fix_unescaped_quotes(cleaned_content),  # Fix quotes
                fix_newlines(cleaned_content),  # Fix newlines
                fix_newlines(fix_unescaped_quotes(cleaned_content))  # Both fixes
            ]
            
            parsed_data = None
            for i, attempt in enumerate(cleaning_attempts):
                try:
                    parsed_data = json.loads(attempt)
                    print(f"Successfully parsed JSON with cleaning strategy {i+1}")
                    break
                except json.JSONDecodeError as attempt_error:
                    print(f"Cleaning strategy {i+1} failed: {str(attempt_error)}")
                    continue
            
            if parsed_data is None:
                # Final fallback: try to extract JSON object manually
                try:
                    # Find the first { and last } to extract JSON object
                    start_idx = cleaned_content.find('{')
                    end_idx = cleaned_content.rfind('}')
                    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                        json_part = cleaned_content[start_idx:end_idx+1]
                        parsed_data = json.loads(json_part)
                        print("Successfully extracted and parsed JSON object")
                    else:
                        raise ValueError("Could not find valid JSON object boundaries")
                except (json.JSONDecodeError, ValueError) as final_error:
                    print(f"Final JSON extraction failed: {str(final_error)}")
                    raise ValueError(f"AI returned invalid JSON after all cleaning attempts. Original error: {str(json_error)}. Raw content preview: {raw_content[:200]}...")
        
        # Log successful completion
        token_usage = {
            'prompt_tokens': input_tokens,
            'completion_tokens': output_tokens,
            'total_tokens': input_tokens + output_tokens
        }
        log.mark_completed(
            response_text=response_text,
            parsed_response=parsed_data,
            token_usage=token_usage
        )
        
        print(f"✅ Multi-source extraction completed using {len(sources)} sources")
        print(f"📊 Token usage: {input_tokens} input + {output_tokens} output = {input_tokens + output_tokens} total")
        
        return parsed_data
        
    except Exception as e:
        # Log error
        log.mark_completed(
            response_text='',
            error=e
        )
        raise e


def format_linkedin_data_for_extraction(linkedin_data):
    """
    Convert LinkedIn data structure to text format for extraction
    """
    if isinstance(linkedin_data, str):
        return linkedin_data
    
    if isinstance(linkedin_data, dict):
        formatted_parts = []
        
        # Basic info
        # Handle both 'name' field and separate 'first_name'/'last_name' fields
        if linkedin_data.get('name'):
            formatted_parts.append(f"Name: {linkedin_data['name']}")
        elif linkedin_data.get('first_name') or linkedin_data.get('last_name'):
            name_parts = []
            if linkedin_data.get('first_name'):
                name_parts.append(linkedin_data['first_name'])
            if linkedin_data.get('last_name'):
                name_parts.append(linkedin_data['last_name'])
            if name_parts:
                formatted_parts.append(f"Name: {' '.join(name_parts)}")
        
        if linkedin_data.get('headline'):
            formatted_parts.append(f"Professional Headline: {linkedin_data['headline']}")
        if linkedin_data.get('location') or linkedin_data.get('geographic_focus'):
            location = linkedin_data.get('location') or linkedin_data.get('geographic_focus')
            formatted_parts.append(f"Location: {location}")
        if linkedin_data.get('summary') or linkedin_data.get('background') or linkedin_data.get('bio'):
            summary = linkedin_data.get('summary') or linkedin_data.get('background') or linkedin_data.get('bio')
            formatted_parts.append(f"Summary: {summary}")
        
        # Add current role and company if available
        if linkedin_data.get('current_role'):
            current_role = linkedin_data['current_role']
            company = linkedin_data.get('company', '')
            if company:
                formatted_parts.append(f"Current Position: {current_role} at {company}")
            else:
                formatted_parts.append(f"Current Position: {current_role}")
                
        # Add LinkedIn URL if available
        if linkedin_data.get('linkedin_url'):
            formatted_parts.append(f"LinkedIn URL: {linkedin_data['linkedin_url']}")
            
        # Add contact information if available
        contact_info = []
        if linkedin_data.get('city'):
            contact_info.append(f"City: {linkedin_data['city']}")
        if linkedin_data.get('state'):
            contact_info.append(f"State: {linkedin_data['state']}")
        if linkedin_data.get('country'):
            contact_info.append(f"Country: {linkedin_data['country']}")
        if contact_info:
            formatted_parts.append("Contact Information: " + ", ".join(contact_info))
            
        # Professional Experience - handle both array and string formats
        # Check for both 'experience' and 'professional_experience' keys
        experience_data = linkedin_data.get('professional_experience') or linkedin_data.get('experience')
        if experience_data:
            if isinstance(experience_data, list):
                formatted_parts.append("Professional Experience:")
                for exp in experience_data:
                    exp_text = f"- {exp.get('title', 'Unknown Title')} at {exp.get('company', 'Unknown Company')}"
                    if exp.get('duration'):
                        exp_text += f" ({exp['duration']})"
                    if exp.get('description'):
                        exp_text += f": {exp['description']}"
                    if exp.get('achievements'):
                        exp_text += f" | Achievements: {exp['achievements']}"
                    formatted_parts.append(exp_text)
            elif isinstance(experience_data, str):
                formatted_parts.append(f"Professional Experience: {experience_data}")
        
        # Education - handle both array and string formats  
        if linkedin_data.get('education'):
            if isinstance(linkedin_data['education'], list):
                formatted_parts.append("Education:")
                for edu in linkedin_data['education']:
                    edu_text = f"- {edu.get('degree', 'Unknown Degree')} from {edu.get('school', 'Unknown School')}"
                    if edu.get('field'):
                        edu_text += f" in {edu['field']}"
                    if edu.get('years'):
                        edu_text += f" ({edu['years']})"
                    if edu.get('description'):
                        edu_text += f" | Description: {edu['description']}"
                    formatted_parts.append(edu_text)
            elif isinstance(linkedin_data['education'], str):
                formatted_parts.append(f"Education: {linkedin_data['education']}")
                
        # Add additional fields from our schema
        if linkedin_data.get('industry_focus'):
            formatted_parts.append(f"Industry Focus: {linkedin_data['industry_focus']}")
        if linkedin_data.get('years_experience'):
            formatted_parts.append(f"Years of Experience: {linkedin_data['years_experience']}")
        if linkedin_data.get('languages'):
            formatted_parts.append(f"Languages: {linkedin_data['languages']}")
        
        # Skills
        if linkedin_data.get('skills'):
            skills_list = linkedin_data['skills'] if isinstance(linkedin_data['skills'], list) else [linkedin_data['skills']]
            formatted_parts.append(f"Skills: {', '.join(skills_list)}")
        
        return '\n'.join(formatted_parts)
    
    return str(linkedin_data)


# -----------------------------------------------------------
# 4. Runner example
# -----------------------------------------------------------

def run_extraction(docx_path):
    print(f"Processing: {docx_path}")
    text = extract_text_from_docx(docx_path)
    result = extract_profile_from_text(text)
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    # CHANGE THESE PATHS TO YOUR FILES
    run_extraction("Grant Williams FINAL BUYER PROFILE - Cohort 59.docx")
    run_extraction("Rob Brubaker and Sheridan Richey PAIR - FINAL Buyer Profile - Cohort 53.docx")
