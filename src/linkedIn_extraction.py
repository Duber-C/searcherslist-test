import os
import json
import sys
import time
import requests
from typing import Any, Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to the path to import Django models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Django setup
import django
from django.conf import settings
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'searcher_api.settings')
    django.setup()

# -----------------------------------------------------------
# 1) Your target schema (same as your GPT extractor)
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
    "value_proposition": "short summary or null",
    "target_statement": "1 sentence with business type, size, geography or null (this is the new unified field for buyer profile content)",
    "areas_of_expertise": "bullet list or null",
    "investment_experience": "string or null",
    "deal_size_preference": "string or null",
    "industry_focus": "summary or null",
    "geographic_focus": "string or null",
    "current_role": "string or null",
    "company": "string or null",
    "years_experience": "string or null",
    "education": "array of objects [{school, degree, field, years, description}, ...] or null",
    "professional_experience": "array of objects [{company, title, duration, description, achievements}, ...] or null",
    "certifications": "summary or null",
    "achievements": "summary or null",
    "website": "string or null",
    "bio": "summary or null",
    "skills": "summary or null",
    "languages": "string or null"
}

# -----------------------------------------------------------
# 2) EnrichLayer LinkedIn fetch
# -----------------------------------------------------------

ENRICHLAYER_API_KEY = os.getenv("ENRICHLAYER_API_KEY")
ENRICHLAYER_PROFILE_URL = os.getenv("ENRICHLAYER_PROFILE_URL")

def fetch_linkedin_profile_json(linkedin_url: str) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {ENRICHLAYER_API_KEY}",
        "Accept": "application/json",
    }
    params = {"url": linkedin_url}

    # Try with increased timeout and retry logic
    max_retries = 3
    timeout = 30  # Increased from 20
    
    for attempt in range(max_retries):
        try:
            print(f"Fetching LinkedIn profile via EnrichLayer for: {linkedin_url} (attempt {attempt + 1}/{max_retries})")
            resp = requests.get(
                ENRICHLAYER_PROFILE_URL,
                headers=headers,
                params=params,
                timeout=timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ReadTimeout as e:
            print(f"Timeout on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # Progressive backoff: 2s, 4s, 6s
                print(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                print(f"All {max_retries} attempts failed due to timeout")
                raise e
        except Exception as e:
            print(f"LinkedIn extraction failed on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                print(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                print(f"All {max_retries} attempts failed")
                raise e

# -----------------------------------------------------------
# 3) Deterministic mapper (personal profile only)
# -----------------------------------------------------------

def _safe_get(d: Dict[str, Any], key: str, default=None):
    return d.get(key, default) if isinstance(d, dict) else default

def _format_date(d: Optional[Dict[str, Any]]) -> Optional[str]:
    if not d:
        return None
    y = d.get("year")
    m = d.get("month")
    day = d.get("day")
    if not y:
        return None
    if m and day:
        return f"{y:04d}-{m:02d}-{day:02d}"
    if m:
        return f"{y:04d}-{m:02d}"
    return f"{y:04d}"

def _pick_current_experience(experiences):
    """
    Prefer ends_at=None, otherwise most recent starts_at.
    """
    if not isinstance(experiences, list) or not experiences:
        return None

    current = [e for e in experiences if _safe_get(e, "ends_at") is None]
    pool = current if current else experiences

    def sort_key(e):
        s = _safe_get(e, "starts_at", {}) or {}
        return (
            s.get("year") or 0,
            s.get("month") or 0,
            s.get("day") or 0,
        )

    return sorted(pool, key=sort_key, reverse=True)[0]

def map_enrichlayer_personal_profile_to_schema(profile_json: Dict[str, Any]) -> Dict[str, Any]:
    public_id = profile_json.get("public_identifier")
    canonical_linkedin_url = f"https://www.linkedin.com/in/{public_id}" if public_id else None

    exp = _pick_current_experience(profile_json.get("experiences", []))
    current_role = _safe_get(exp, "title")
    company = _safe_get(exp, "company")

    # Education structured data
    edu_list = profile_json.get("education", [])
    education = None
    if isinstance(edu_list, list) and edu_list:
        education_array = []
        for e in edu_list:
            school = _safe_get(e, "school")
            degree = _safe_get(e, "degree_name")
            field = _safe_get(e, "field_of_study")
            start = _format_date(_safe_get(e, "starts_at"))
            end = _format_date(_safe_get(e, "ends_at"))
            
            years = None
            if start and end:
                years = f"{start} - {end}"
            elif start and not end:
                years = f"{start} - Present"
            elif end and not start:
                years = f"Until {end}"

            if school or degree or field:  # Only add if we have meaningful data
                education_array.append({
                    "school": school,
                    "degree": degree,
                    "field": field,
                    "years": years,
                    "description": None  # LinkedIn doesn't typically have education descriptions
                })
        education = education_array if education_array else None

    # Professional Experience structured data
    exp_list = profile_json.get("experiences", [])
    professional_experience = None
    if isinstance(exp_list, list) and exp_list:
        experience_array = []
        for e in exp_list:
            company = _safe_get(e, "company")
            title = _safe_get(e, "title")
            location = _safe_get(e, "location")
            description = _safe_get(e, "description")
            start = _format_date(_safe_get(e, "starts_at"))
            end = _format_date(_safe_get(e, "ends_at"))
            
            duration = None
            if start and end:
                duration = f"{start} - {end}"
            elif start and not end:
                duration = f"{start} - Present"
            elif end and not start:
                duration = f"Until {end}"

            if company or title:  # Only add if we have meaningful data
                experience_array.append({
                    "company": company,
                    "title": title,
                    "duration": duration,
                    "description": description,
                    "achievements": None  # Could parse from description in the future
                })
        professional_experience = experience_array if experience_array else None

    # Languages
    langs = profile_json.get("languages") or profile_json.get("languages_and_proficiencies") or []
    languages = None
    if isinstance(langs, list) and langs:
        if all(isinstance(x, str) for x in langs):
            languages = ", ".join(langs)
        else:
            names = []
            for x in langs:
                name = _safe_get(x, "name") or _safe_get(x, "language")
                prof = _safe_get(x, "proficiency")
                if name and prof:
                    names.append(f"{name} ({prof})")
                elif name:
                    names.append(name)
            languages = ", ".join(names) if names else None

    # Skills
    skills_list = profile_json.get("skills", [])
    skills = None
    if isinstance(skills_list, list) and skills_list:
        if all(isinstance(x, str) for x in skills_list):
            skills = ", ".join(skills_list)
        else:
            names = [x.get("name") for x in skills_list if isinstance(x, dict) and x.get("name")]
            skills = ", ".join(names) if names else None

    country = profile_json.get("country_full_name") or profile_json.get("country")

    return {
        "first_name": profile_json.get("first_name"),
        "last_name": profile_json.get("last_name"),
        "phone_number": None,  # personal_numbers exists but may be empty
        "country": country,
        "city": profile_json.get("city"),
        "state": profile_json.get("state"),
        "linkedin_url": canonical_linkedin_url,  # use canonical if possible
        "background": profile_json.get("summary"),
        "value_proposition": None,
        "areas_of_expertise": None,
        "investment_experience": None,
        "deal_size_preference": None,
        "industry_focus": profile_json.get("industry"),
        "geographic_focus": profile_json.get("location_str"),
        "current_role": current_role,
        "company": company,
        "years_experience": None,
        "education": education,
        "professional_experience": professional_experience,
        "certifications": None,
        "achievements": None,
        "website": None,
        "bio": profile_json.get("summary") or profile_json.get("headline"),
        "skills": skills,
        "languages": languages,
    }

# -----------------------------------------------------------
# 4) Runner (individual test)
# -----------------------------------------------------------

def run_linkedin_extraction(linkedin_url: str):
    print(f"Fetching LinkedIn profile via EnrichLayer for: {linkedin_url}")
    raw = fetch_linkedin_profile_json(linkedin_url)
    mapped = map_enrichlayer_personal_profile_to_schema(raw)

    print("\n--- MAPPED PROFILE (schema) ---")
    print(json.dumps(mapped, indent=2, ensure_ascii=False))
    return mapped


if __name__ == "__main__":
    # Example LinkedIn URL (replace with the one you want to test)
    LINKEDIN_URL = "https://www.linkedin.com/in/morcio/"
    run_linkedin_extraction(LINKEDIN_URL)
