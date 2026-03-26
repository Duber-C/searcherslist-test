from django.urls import path
from users.views.ai import ai_profile_extraction, linkedin_import, multi_source_extraction
from users.views.auth import debug_resolve_token, send_otp, verify_otp_general
from users.views.health_check import health_check
from users.views.otp import verify_otp
from users.views.profile import (
    UserListView,
    UserProfileView,
    UserRegistrationView,
    create_profile,
    get_user_profile,
    public_profile_view,
    user_dashboard
)
from users.views.profile_sections import (
    save_professional_experience_data,
    update_basic_info,
    update_education,
    update_expertise,
    update_location,
    update_professional_experience,
    update_profile_section,
    update_target_statement,
    update_value_proposition,
)
from users.views.publish import publish_profile, publish_profile_dev, unpublish_profile
from users.views.questionnaire import get_questions_list, test_questionnaire_answers
from users.views.signed_links import create_signed_link, validate_signed_link
from users.views.support import create_support_ticket


app_name = 'users'

urlpatterns = [
    # Health check
    path('health/', health_check, name='health_check'),
    
    # OTP endpoints for general access (using OTPVerification model)
    path('send-otp/', send_otp, name='send_otp'),
    path('verify-otp/', verify_otp_general, name='verify_otp'),
    
    # User registration and profile management
    path('register/', UserRegistrationView.as_view(), name='user_register'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('list/', UserListView.as_view(), name='user_list'),
    path('dashboard/', user_dashboard, name='user_dashboard'),
    
    # Simple endpoint matching frontend form
    path('create-profile/', create_profile, name='create_profile'),
    path('get-profile/', get_user_profile, name='get_user_profile'),
    
    # Individual section updates
    path('update-profile/<str:section_name>/', update_profile_section, name='update_profile_section'),
    path('update-basic-info/', update_basic_info, name='update_basic_info'),
    path('update-location/', update_location, name='update_location'),
    path('update-target-statement/', update_target_statement, name='update_target_statement'),
    path('update-value-proposition/', update_value_proposition, name='update_value_proposition'),
    path('update-expertise/', update_expertise, name='update_expertise'),
    path('update-professional-experience/', update_professional_experience, name='update_professional_experience'),
    path('update-education/', update_education, name='update_education'),
    
    # AI Profile Extraction
    path('ai-profile-extraction/', ai_profile_extraction, name='ai_profile_extraction'),
    path('linkedin-import/', linkedin_import, name='linkedin_import'),
    path('multi-source-extraction/', multi_source_extraction, name='multi_source_extraction'),
    
    # Professional experience data management
    path('save-professional-experience/', save_professional_experience_data, name='save_professional_experience'),
    
    # Questions and Questionnaire
    path('questions/', get_questions_list, name='get_questions_list'),
    path('test-questionnaire/', test_questionnaire_answers, name='test_questionnaire_answers'),
    
    # Signed Links
    path('validate-signed-link/', validate_signed_link, name='validate_signed_link'),
    # path('create-signed-link/', create_signed_link, name='create_signed_link'),
    # path('verify-access-code/', verify_otp, name='verify_access_code'),

    # public profile lookup by opaque token (not raw email)
    # Support both token route and the no-token route which will return the
    # authenticated user's public profile when present.
    path('public-profile/<str:token>/', public_profile_view, name='public_profile_view'),
    path('public-profile/', public_profile_view, name='public_profile_current'),
    path('publish-profile/', publish_profile, name='publish_profile'), # duplicated
    path('publish-profile-dev/', publish_profile_dev, name='publish_profile_dev'),

    # Debug: resolve bearer token to user (development only)
    path('debug-token/', debug_resolve_token, name='debug_resolve_token'), # duplicated

    # Unpublish profile (remove public token)
    path('unpublish-profile/', unpublish_profile, name='unpublish_profile'),
    path("support/contact/", create_support_ticket, name="support_contact"),
]
