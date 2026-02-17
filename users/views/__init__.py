"""Package for split user views.

This package exposes commonly-used view callables from the submodules so that
code importing `from users import views` or `from users.views import <name>`
keeps working while the implementation is split across multiple files.
"""

# Prefer explicit imports from the modular view files. Many implementations
# were moved into `all_views.py` during refactor; import that first.
from .all_views import *

# Import additional focused modules (these may override names from all_views
# but are kept explicit for clarity).
from .auth import send_otp, verify_otp_general, verify_otp
from .publish import publish_profile, unpublish_profile
from .profile_sections import (
    update_basic_info, update_location, update_target_statement,
    update_value_proposition, update_expertise, update_professional_experience,
    update_education, update_profile_section
)
from .profile import user_dashboard
from .ai import ai_profile_extraction, linkedin_import, multi_source_extraction
from .questionnaire import get_questions_list, test_questionnaire_answers
from .signed_links import create_signed_link, validate_signed_link

# Export the most commonly referenced view names used by the URLconf.
__all__ = [
    'health_check',
    'send_otp', 'verify_otp_general', 'verify_otp',
    'UserRegistrationView', 'UserProfileView', 'UserListView', 'user_dashboard',
    'create_profile', 'get_user_profile',
    'update_profile_section', 'update_basic_info', 'update_location',
    'update_target_statement', 'update_value_proposition', 'update_expertise',
    'update_professional_experience', 'update_education',
    'ai_profile_extraction', 'linkedin_import', 'multi_source_extraction',
    'save_professional_experience_data',
    'get_questions_list', 'test_questionnaire_answers',
    'create_signed_link', 'validate_signed_link',
    'public_profile_view',
    'publish_profile', 'unpublish_profile',
    'debug_resolve_token'
]
