"""
users.views package public API for URL routing.

`users/urls.py` does `from . import views`, so everything referenced there must be
imported and re-exported here.
"""

# ---- Health ----
from .health_check import health_check  # create this file or change back to all_views import

# ---- OTP / auth ----
from .auth import send_otp, verify_otp_general, verify_otp, debug_resolve_token

# ---- Profile (registration + core profile endpoints) ----
from .profile import (
    public_profile_view,
    UserRegistrationView,
    UserProfileView,
    UserListView,
    create_profile,
    get_user_profile,
    user_dashboard,
)

# ---- Section endpoints ----
from .profile_sections import (
    update_profile_section,
    update_basic_info,
    update_location,
    update_target_statement,
    update_value_proposition,
    update_expertise,
    update_professional_experience,
    update_education,
    # If you move it here later:
    # save_professional_experience_data,
)

# If this still lives in all_views.py today, keep importing from there until moved:
from .all_views import save_professional_experience_data

# ---- Publish/unpublish ----
from .publish import publish_profile, unpublish_profile, publish_profile_dev

# ---- AI endpoints ----
from .ai import ai_profile_extraction, linkedin_import, multi_source_extraction

# ---- Questionnaire ----
from .questionnaire import get_questions_list, test_questionnaire_answers

# ---- Signed links ----
from .signed_links import create_signed_link, validate_signed_link

__all__ = [
    "health_check",
    "send_otp",
    "verify_otp_general",
    "verify_otp",
    "debug_resolve_token",
    "public_profile_view",
    "UserRegistrationView",
    "UserProfileView",
    "UserListView",
    "create_profile",
    "get_user_profile",
    "user_dashboard",
    "update_profile_section",
    "update_basic_info",
    "update_location",
    "update_target_statement",
    "update_value_proposition",
    "update_expertise",
    "update_professional_experience",
    "update_education",
    "ai_profile_extraction",
    "linkedin_import",
    "multi_source_extraction",
    "save_professional_experience_data",
    "get_questions_list",
    "test_questionnaire_answers",
    "create_signed_link",
    "validate_signed_link",
    "publish_profile",
    "publish_profile_dev",
    "unpublish_profile",
]