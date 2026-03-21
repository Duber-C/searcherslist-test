from django.urls import path
from . import views
from . import otp_views
from . import support_views

app_name = 'users'

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health_check'),
    
    # OTP endpoints for general access (using OTPVerification model)
    path('send-otp/', views.send_otp, name='send_otp'),
    path('verify-otp/', views.verify_otp_general, name='verify_otp'),
    
    # User registration and profile management
    path('register/', views.UserRegistrationView.as_view(), name='user_register'),
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('list/', views.UserListView.as_view(), name='user_list'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    
    # Simple endpoint matching frontend form
    path('create-profile/', views.create_profile, name='create_profile'),
    path('get-profile/', views.get_user_profile, name='get_user_profile'),
    
    # Individual section updates
    path('update-profile/<str:section_name>/', views.update_profile_section, name='update_profile_section'),
    path('update-basic-info/', views.update_basic_info, name='update_basic_info'),
    path('update-location/', views.update_location, name='update_location'),
    path('update-target-statement/', views.update_target_statement, name='update_target_statement'),
    path('update-value-proposition/', views.update_value_proposition, name='update_value_proposition'),
    path('update-expertise/', views.update_expertise, name='update_expertise'),
    path('update-professional-experience/', views.update_professional_experience, name='update_professional_experience'),
    path('update-education/', views.update_education, name='update_education'),
    
    # AI Profile Extraction
    path('ai-profile-extraction/', views.ai_profile_extraction, name='ai_profile_extraction'),
    path('linkedin-import/', views.linkedin_import, name='linkedin_import'),
    path('multi-source-extraction/', views.multi_source_extraction, name='multi_source_extraction'),
    
    # Professional experience data management
    path('save-professional-experience/', views.save_professional_experience_data, name='save_professional_experience'),
    
    # Questions and Questionnaire
    path('questions/', views.get_questions_list, name='get_questions_list'),
    path('test-questionnaire/', views.test_questionnaire_answers, name='test_questionnaire_answers'),
    
    # Signed Links
    path('create-signed-link/', views.create_signed_link, name='create_signed_link'),
    path('validate-signed-link/', views.validate_signed_link, name='validate_signed_link'),
    path('verify-access-code/', views.verify_otp, name='verify_access_code'),
    # public profile lookup by opaque token (not raw email)
    # Support both token route and the no-token route which will return the
    # authenticated user's public profile when present.
    path('public-profile/<str:token>/', views.public_profile_view, name='public_profile_view'),
    path('public-profile/', views.public_profile_view, name='public_profile_current'),
    path('publish-profile/', views.publish_profile, name='publish_profile'),
    path('publish-profile-dev/', views.publish_profile_dev, name='publish_profile_dev'),
    # Debug: resolve bearer token to user (development only)
    path('debug-token/', views.debug_resolve_token, name='debug_resolve_token'),
    # Unpublish profile (remove public token)
    path('unpublish-profile/', views.unpublish_profile, name='unpublish_profile'),
    path("support/contact/", support_views.create_support_ticket, name="support_contact"),
]