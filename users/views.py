"""
Top-level views re-export module.
All implementations live under `users.views` package submodules (profile, auth, publish, questionnaire, signed_links, etc.).
This module only re-exports selected names so existing URL imports continue to work.
"""

# Profile views
from .views.profile import (
    public_profile_view,
    UserRegistrationView,
    UserProfileView,
    UserListView,
    create_profile,
    get_user_profile,
    user_dashboard,
)

# Auth / OTP
from .views.auth import send_otp, verify_otp_general, verify_otp, debug_resolve_token

# Publish (publish/unpublish)
from .views.publish import publish_profile, unpublish_profile, publish_profile_dev

# Questionnaire
from .views.questionnaire import get_questions_list, test_questionnaire_answers

# Signed links
from .views.signed_links import create_signed_link, validate_signed_link

# Section endpoints
from .views.profile_sections import (
    update_basic_info, update_location, update_target_statement,
    update_value_proposition, update_expertise, update_professional_experience,
    update_education, update_profile_section
)
# AI endpoints (moved to users.views.ai)
from .views.ai import ai_profile_extraction, linkedin_import, multi_source_extraction

__all__ = [
    # Profile
    'public_profile_view', 'UserRegistrationView', 'UserProfileView', 'UserListView',
    'create_profile', 'get_user_profile', 'user_dashboard',
    # Auth
    'send_otp', 'verify_otp_general', 'verify_otp', 'debug_resolve_token',
    # Publish
    'publish_profile', 'unpublish_profile', 'publish_profile_dev',
    # Questionnaire
    'get_questions_list', 'test_questionnaire_answers',
    # Signed Links
    'create_signed_link', 'validate_signed_link',
     # Section updates
    'update_basic_info', 'update_location', 'update_target_statement', 'update_value_proposition', 'update_expertise', 'update_professional_experience', 'update_education', 'update_profile_section'
    , 'ai_profile_extraction', 'linkedin_import', 'multi_source_extraction'
]

"""
Lightweight re-export module for views. Implementations live under `users.views` package.
This file intentionally exposes view names from submodules so URL imports remain unchanged.
"""

# Profile views
from .views.profile import (
    public_profile_view,
    UserRegistrationView,
    UserProfileView,
    UserListView,
    create_profile,
    get_user_profile,
    user_dashboard,
)

# Auth / OTP
from .views.auth import send_otp, verify_otp_general, verify_otp, debug_resolve_token

# Publish (publish/unpublish)
from .views.publish import publish_profile, unpublish_profile, publish_profile_dev

# Questionnaire
from .views.questionnaire import get_questions_list, test_questionnaire_answers

# Signed links
from .views.signed_links import create_signed_link, validate_signed_link

# Fallback: any legacy or not-yet-moved views
from .views.all_views import *

__all__ = [
    # Profile
    'public_profile_view', 'UserRegistrationView', 'UserProfileView', 'UserListView',
    'create_profile', 'get_user_profile', 'user_dashboard',
    # Auth
    'send_otp', 'verify_otp_general', 'verify_otp', 'debug_resolve_token',
    # Publish
    'publish_profile', 'unpublish_profile', 'publish_profile_dev',
    # Questionnaire
    'get_questions_list', 'test_questionnaire_answers',
    # Signed Links
    'create_signed_link', 'validate_signed_link'
]
    
class UserRegistrationView(generics.CreateAPIView):
    """
    API endpoint for user registration
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user_data = UserSerializer(user).data
            return Response({
                'message': 'Profile created successfully!',
                'user': user_data,
                'profile_id': user.id
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'message': 'Error creating profile. Please check your information.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for retrieving and updating user profile
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserSerializer
        return UserUpdateSerializer


class UserListView(generics.ListAPIView):
    """
    API endpoint for listing all users (admin only)
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Only allow superusers to see all users
        if self.request.user.is_superuser:
            return User.objects.all()
        else:
            # Regular users can only see their own profile
            return User.objects.filter(id=self.request.user.id)


def normalize_array_fields(data):
    """
    Normalize education and professional_experience arrays to ensure consistent structure
    """
    if 'education' in data and isinstance(data['education'], list):
        normalized_education = []
        for edu in data['education']:
            if edu and isinstance(edu, dict):
                normalized_edu = {
                    'school': str(edu.get('school', 'Unknown')).strip() or 'Unknown',
                    'degree': str(edu.get('degree', 'Unknown')).strip() or 'Unknown',
                    'field': str(edu.get('field', 'General')).strip() or 'General',
                    'years': str(edu.get('years', 'Unknown')).strip() or 'Unknown',
                    'description': str(edu.get('description', 'None')).strip() or 'None'
                }
                # Convert null strings back to proper values
                for key, value in normalized_edu.items():
                    if value.lower() in ['null', 'none', '']:
                        if key == 'degree':
                            normalized_edu[key] = 'Unknown'
                        elif key == 'field':
                            normalized_edu[key] = 'General'
                        elif key == 'description':
                            normalized_edu[key] = 'None'
                        else:
                            normalized_edu[key] = 'Unknown'
                
                normalized_education.append(normalized_edu)
        data['education'] = normalized_education

    if 'professional_experience' in data and isinstance(data['professional_experience'], list):
        normalized_experience = []
        for exp in data['professional_experience']:
            if exp and isinstance(exp, dict):
                normalized_exp = {
                    'company': str(exp.get('company', 'Unknown')).strip() or 'Unknown',
                    'title': str(exp.get('title', 'Unknown')).strip() or 'Unknown', 
                    'duration': str(exp.get('duration', 'Unknown')).strip() or 'Unknown',
                    'description': str(exp.get('description', 'None')).strip() or 'None',
                    'achievements': str(exp.get('achievements', 'None')).strip() or 'None'
                }
                # Convert null strings back to proper values
                for key, value in normalized_exp.items():
                    if value.lower() in ['null', 'none', '']:
                        if key in ['description', 'achievements']:
                            normalized_exp[key] = 'None'
                        else:
                            normalized_exp[key] = 'Unknown'
                
                normalized_experience.append(normalized_exp)
        data['professional_experience'] = normalized_experience

    return data


def map_frontend_fields(data, updating_existing_user=False):
    """
    Map frontend camelCase fields to backend snake_case fields
    """
    field_mapping = {
        'firstName': 'first_name',
        'lastName': 'last_name', 
        'phoneNumber': 'phone_number',
        'linkedinUrl': 'linkedin_url',
        'currentRole': 'current_role',
        'yearsExperience': 'years_experience',
        'valueProposition': 'value_proposition',
        'areasOfExpertise': 'areas_of_expertise',
        'investmentExperience': 'investment_experience',
        'dealSizePreference': 'deal_size_preference',
        'industryFocus': 'industry_focus',
        'geographicFocus': 'geographic_focus',
        'acquisitionTarget': 'acquisition_target',
        'acquisitionTargetRaw': 'existing_buyer_profile',
        # Add other mappings as needed
    }
    
    mapped_data = {}
    for key, value in data.items():
        backend_field = field_mapping.get(key, key)
        mapped_data[backend_field] = value
    
    # Handle username properly
    if updating_existing_user:
        # Remove username completely when updating existing user to avoid constraint issues
        mapped_data.pop('username', None)
        print(f"DEBUG: Removed username from data for existing user update")
    else:
        # Auto-generate username from email only for new users
        if 'email' in mapped_data and 'username' not in mapped_data:
            mapped_data['username'] = mapped_data['email']
    
    # Normalize array fields for consistent structure
    mapped_data = normalize_array_fields(mapped_data)
    
    return mapped_data


@api_view(['POST'])
@permission_classes([AllowAny])
def create_profile(request):
    """
    Create or update user profile
    Handles both new users and users with verified emails
    """
    print(f"🚀 CREATE_PROFILE called!")
    print(f"🔍 Raw request.data: {request.data}")
    print(f"🔍 Request method: {request.method}")
    print(f"🔍 Content-Type: {request.content_type}")
    
    # Debug professional experience specifically
    if 'professional_experience' in request.data:
        prof_exp = request.data['professional_experience']
        print(f"💼 Professional experience received:")
        print(f"   Type: {type(prof_exp)}")
        print(f"   Length: {len(prof_exp) if isinstance(prof_exp, (list, dict)) else 'N/A'}")
        print(f"   Content: {prof_exp}")
    else:
        print(f"❌ No 'professional_experience' field in request.data")
    
    # Map frontend fields to backend fields
    email = request.data.get('email')
    user_exists = User.objects.filter(email=email).exists() if email else False
    
    print(f"📧 Email: {email}")
    print(f"👤 User exists: {user_exists}")
    
    mapped_data = map_frontend_fields(request.data, updating_existing_user=user_exists)
    print(f"🗺️  Mapped data: {mapped_data}")
    
    # Debug professional experience after mapping
    if 'professional_experience' in mapped_data:
        prof_exp_mapped = mapped_data['professional_experience']
        print(f"💼 Professional experience after mapping:")
        print(f"   Type: {type(prof_exp_mapped)}")
        print(f"   Length: {len(prof_exp_mapped) if isinstance(prof_exp_mapped, (list, dict)) else 'N/A'}")
        print(f"   Content: {prof_exp_mapped}")
    else:
        print(f"❌ No 'professional_experience' field in mapped_data")
    
    email_verified = mapped_data.get('email_verified') == 'true'
    print(f"✅ Email verified: {email_verified}")
    
    # Always try to find existing user first
    try:
        user = User.objects.get(email=email)
        print(f"🔄 Updating existing user: {user.email} (ID: {user.id})")
        # Update existing user (especially for incomplete profiles)
        serializer = UserRegistrationSerializer(
            user, 
            data=mapped_data, 
            partial=True,
            context={'email_verified': email_verified, 'updating_existing': True}
        )
    except User.DoesNotExist:
        print(f"🆕 Creating new user for: {email}")
        # Create new user only if user doesn't exist
        if email_verified:
            serializer = UserRegistrationSerializer(
                data=mapped_data,
                context={'email_verified': True}
            )
        else:
            # Regular creation with full validation
            serializer = UserRegistrationSerializer(data=mapped_data)
    
    if serializer.is_valid():
        print(f"✅ Serializer is valid!")
        try:
            user = serializer.save()
            print(f"💾 User saved successfully: {user.email} (ID: {user.id})")
            
            # If the frontend explicitly requested marking the profile completed, honor it.
            # Otherwise, fall back to auto-detection via `mark_profile_complete()`.
            profile_complete = False
            try:
                requested_complete = mapped_data.get('profile_completed')
                if requested_complete is not None:
                    if isinstance(requested_complete, str):
                        requested_complete = requested_complete.lower() in ['true', '1', 'yes', 'on']
                    requested_complete = bool(requested_complete)
                if requested_complete:
                    user.profile_completed = True
                    user.save(update_fields=['profile_completed'])
                    profile_complete = True
                    print(f"📋 Profile explicitly marked complete by request for user {user.email}")
                else:
                    profile_complete = user.mark_profile_complete()
                    print(f"📋 Profile complete status (auto): {profile_complete}")
            except Exception as e:
                print(f"❌ Error while setting profile completion: {str(e)}")
                profile_complete = user.mark_profile_complete()
            
            return Response({
                'message': 'Profile saved successfully!',
                'profile_id': f'profile_{user.id}',
                'profile_completed': profile_complete,
                'user': {
                    'id': user.id,
                    'name': f'{user.first_name} {user.last_name}',
                    'email': user.email,
                    'phone': user.phone_number,
                    'location': f'{user.city}, {user.state}, {user.country}',
                    'linkedin': user.linkedin_url,
                    'profile_completed': user.profile_completed,
                    'created_at': user.created_at.isoformat()
                }
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            print(f"❌ Error saving user: {str(e)}")
            import traceback
            print(f"📋 Full traceback: {traceback.format_exc()}")
            return Response({
                'message': 'Error creating profile. Please try again.',
                'error': str(e),
                'debug_info': {
                    'email_verified': email_verified,
                    'email': email,
                    'user_exists': User.objects.filter(email=email).exists()
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    print(f"❌ Serializer validation failed!")
    print(f"🚫 Serializer errors: {serializer.errors}")
    return Response({
        'message': 'Invalid data provided. Please check your information.',
        'errors': serializer.errors,
        'debug_info': {
            'email_verified': email_verified,
            'email': email
        }
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def get_user_profile(request):
    """
    Get existing user profile data for prefilling forms
    """
    email = request.GET.get('email')
    
    if not email:
        return Response({
            'success': False,
            'message': 'Email parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
        
        return Response({
            'success': True,
            'user_exists': True,
            'profile_completed': user.profile_completed,
            'data': {
                'id': user.id,
                'email': user.email,
                'firstName': user.first_name,
                'lastName': user.last_name,
                'phoneNumber': user.phone_number,
                'country': user.country,
                'city': user.city,
                'state': user.state,
                'linkedinUrl': user.linkedin_url,
                'background': user.background,
                # Professional fields
                'valueProposition': user.value_proposition,
                'areasOfExpertise': user.areas_of_expertise,
                'investmentExperience': user.investment_experience,
                'dealSizePreference': user.deal_size_preference,
                'industryFocus': user.industry_focus,
                'geographicFocus': user.geographic_focus,
                'currentRole': user.current_role,
                'company': user.company,
                'yearsExperience': user.years_experience,
                'education': user.education,
                'professionalExperience': user.professional_experience,
                'certifications': user.certifications,
                'achievements': user.achievements,
                'acquisitionTarget': user.acquisition_target,
                'acquisitionTargetRaw': user.existing_buyer_profile,
                'website': user.website,
                'bio': user.bio,
                'skills': user.skills,
                'languages': user.languages,
                'profileCompleted': user.profile_completed,
                'published': user.published,
                'createdAt': user.created_at.isoformat(),
                'updatedAt': user.updated_at.isoformat(),
                # File URLs if they exist
                'resumeUrl': user.resume.url if user.resume else None,
                'buyerProfileUrl': user.buyer_profile.url if user.buyer_profile else None,
                'publicToken': str(user.public_token) if user.public_token else None,
            }
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'success': True,
            'user_exists': False,
            'profile_completed': False,
            'data': {}
        }, status=status.HTTP_200_OK)



# publish_profile and unpublish_profile have been moved to `users/views_publish.py`


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def publish_profile_dev(request):
    """
    Development-only publish endpoint: publish profile by email without authentication.
    Only available when `settings.DEBUG` is True.
    """
    try:
        if not getattr(settings, 'DEBUG', False):
            return Response({'success': False, 'message': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)

        email = request.data.get('email')
        if not email:
            return Response({'success': False, 'message': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'success': False, 'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        user.published = True
        if not user.profile_completed:
            user.profile_completed = True
            user.save(update_fields=['published', 'profile_completed'])
        else:
            user.save(update_fields=['published'])

        # Generate public token if missing
        if not user.public_token:
            user.public_token = uuid.uuid4()
            user.save(update_fields=['public_token'])

        return Response({'success': True, 'message': 'Profile published (dev)', 'published': user.published, 'public_token': str(user.public_token)}, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"❌ Error in publish_profile_dev: {e}")
        return Response({'success': False, 'message': 'Error publishing profile (dev)', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Simple health check endpoint
    """
    return Response({
        'status': 'healthy',
        'message': 'Searcher API is running',
        'version': '1.0.0'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def debug_resolve_token(request):
    """
    Development-only endpoint to resolve a Bearer token to a User and return debug info.
    Only available when settings.DEBUG is True.
    """
    try:
        if not getattr(settings, 'DEBUG', False):
            return Response({'success': False, 'message': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)

        auth = request.META.get('HTTP_AUTHORIZATION') or request.META.get('Authorization')
        if not auth or not isinstance(auth, str) or not auth.lower().startswith('bearer '):
            return Response({'success': False, 'message': 'Authorization Bearer token required'}, status=status.HTTP_400_BAD_REQUEST)

        token = auth.split(None, 1)[1].strip()
        masked = f"****{token[-6:]}" if len(token) > 6 else token
        print(f"🔍 debug_resolve_token received masked token: {masked}")

        resolved_user = None
        try:
            resolved_user = User.objects.filter(api_token=token).first()
            if resolved_user:
                print(f"✅ Token resolved to user: {resolved_user.email} (ID: {resolved_user.id})")
        except Exception as e:
            print(f"❌ Error resolving token to user: {e}")

        # Build a safe user_info payload from request.user
        user_info = None
        try:
            u = request.user
            if u and getattr(u, 'is_authenticated', False):
                user_info = {
                    'email': getattr(u, 'email', None),
                    'id': getattr(u, 'id', None),
                    'published': getattr(u, 'published', None),
                    'profile_completed': getattr(u, 'profile_completed', None),
                    'public_token': str(getattr(u, 'public_token', None)) if getattr(u, 'public_token', None) else None,
                }
            else:
                user_info = None
        except Exception as e:
            print(f"❌ Error building user_info from request.user: {e}")
            user_info = None

        return Response({'token': token, 'resolved_user': resolved_user and resolved_user.email, 'user': user_info}, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"💥 debug_resolve_token error: {e}")
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def send_otp(request):
    """
    Send OTP to email address - only if email exists in signed_links or users table
    """
    email = request.data.get('email')
    
    if not email:
        return Response({
            'success': False,
            'message': 'Email is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    print(f"🔍 send_otp: received request for {email}")

    # If user doesn't exist, create a minimal user record with only email
    try:
        user, created = User.objects.get_or_create(email=email, defaults={'username': email})
        if created:
            print(f"🆕 Created minimal user record for {email}")
    except Exception as e:
        print(f"❌ Error ensuring user exists for {email}: {e}")
        return Response({
            'success': False,
            'message': 'Server error while creating user',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    try:
        # Invalidate any existing unused OTPs for this email
        existing_otps = OTPVerification.objects.filter(email=email, used=False)
        if existing_otps.exists():
            print(f"🔄 Invalidating {existing_otps.count()} existing OTPs for {email}")
            existing_otps.update(used=True, used_at=timezone.now())
        
        # Create new OTP using the new OTPVerification model
        otp_verification = OTPVerification.objects.create(
            email=email,
            signed_link=None  # Can be null for existing users
        )
        
        print(f"✅ Created new OTP for {email}: {otp_verification.otp_code}")
        
        # Send OTP email
        try:
            send_mail(
                subject='Your Access Code - Searcher Platform',
                message=f'Your access code is: {otp_verification.otp_code}\\n\\nThis code will expire in 10 minutes.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=f'''
                <html>
                <body>
                    <h2>Your Access Code</h2>
                    <p>Your access code for the Searcher Platform is:</p>
                    <h1 style="color: #007bff; font-size: 36px; text-align: center; margin: 20px 0;">{otp_verification.otp_code}</h1>
                    <p>This code will expire in 10 minutes.</p>
                    <p>If you didn't request this code, please ignore this email.</p>
                </body>
                </html>
                ''',
                fail_silently=False,
            )
            print(f"📧 OTP sent to {email}: {otp_verification.otp_code}")
        except Exception as e:
            print(f"❌ Failed to send OTP email: {e}")
            # In development, keep the OTP and return it in the response for debugging/testing
            try:
                debug_mode = bool(getattr(settings, 'DEBUG', False))
            except Exception:
                debug_mode = False

            if debug_mode:
                print(f"🛠 DEBUG MODE: returning OTP code in response for {email}")
                return Response({
                    'success': True,
                    'message': 'Access code generated (debug mode).',
                    'email': email,
                    'user_exists': User.objects.filter(email=email).exists(),
                    'otp_code': otp_verification.otp_code
                }, status=status.HTTP_200_OK)

            otp_verification.delete()
            return Response({
                'success': False,
                'message': 'Failed to send access code. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'success': True,
            'message': 'Access code sent to your email',
            'email': email,
            'user_exists': User.objects.filter(email=email).exists()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"💥 Error creating OTP: {e}")
        return Response({
            'success': False,
            'message': 'Error generating access code. Please try again.',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp_general(request):
    """
    Verify OTP code for general access (from homepage)
    """
    try:
        email = request.data.get('email')
        otp_code = request.data.get('otp_code')
        
        print(f"🔍 BACKEND DEBUG - Verifying general OTP:")
        print(f"Email: {email}")
        print(f"OTP Code: {otp_code}")
        
        if not email or not otp_code:
            print("❌ Missing email or OTP code")
            return Response({
                'success': False,
                'message': 'Email and OTP code are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        # No authorization check here - users may be created at send_otp time
        
        try:
            # Get the most recent valid OTP for this email
            otp_verification = OTPVerification.objects.filter(
                email=email,
                otp_code=otp_code,
                used=False
            ).order_by('-created_at').first()
            
            if not otp_verification:
                print("❌ OTP not found or already used")
                return Response({
                    'success': False,
                    'message': 'Invalid or expired access code'
                }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            return Response({
                'success': False,
                'message': 'Invalid access code'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if not otp_verification.is_valid():
            reason = "already used" if otp_verification.used else "expired"
            print(f"❌ OTP is {reason}")
            return Response({
                'success': False,
                'message': f'Access code is {reason}. Please request a new one.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Mark OTP as used
        otp_verification.mark_as_used()

        print(f"✅ OTP verified successfully for {email}")

        # Determine user status and create an API bearer token for the frontend
        api_token = None
        try:
            user, created = User.objects.get_or_create(email=email, defaults={'username': email})
            if user.profile_completed:
                account_status = 'finished'
                next_action = 'dashboard'
            else:
                account_status = 'incomplete'
                next_action = 'complete_profile'

            # Generate a secure API token (64 hex chars)
            try:
                api_token = secrets.token_hex(32)
                user.api_token = api_token
                user.save(update_fields=['api_token'])
            except Exception as e:
                print(f"❌ Failed to generate/save api_token for {email}: {e}")

        except User.DoesNotExist:
            account_status = 'new'
            next_action = 'create_profile'

        return Response({
            'success': True,
            'message': 'OTP verified successfully!',
            'email': email,
            'account_status': account_status,
            'next_action': next_action,
            'user_exists': account_status != 'new',
            'api_token': api_token
        })
        
    except Exception as e:
        print(f"💥 BACKEND ERROR: {str(e)}")
        return Response({
            'success': False,
            'message': f'Server error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    """
    Verify OTP code
    """
    serializer = VerifyOTPSerializer(data=request.data)
    
    if serializer.is_valid():
        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp_code']
        
        try:
            # Get the most recent valid OTP for this email
            otp = OTP.get_valid_otp(email)
            
            if not otp:
                return Response({
                    'success': False,
                    'message': 'No valid OTP found. Please request a new one.',
                    'require_new_otp': True
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Verify the OTP
            is_valid, message = otp.verify(otp_code)
            
            if is_valid:
                if otp.user_exists:
                    # Existing user - check profile completion to determine action
                    user = otp.user
                    user_data = UserSerializer(user).data

                    # generate api_token for frontend to use as bearer token
                    api_token = None
                    try:
                        api_token = secrets.token_hex(32)
                        user.api_token = api_token
                        user.save(update_fields=['api_token'])
                    except Exception as e:
                        print(f"❌ Failed to generate/save api_token for {user.email}: {e}")

                    if user.profile_completed:
                        # Complete profile - redirect to dashboard
                        return Response({
                            'success': True,
                            'message': 'OTP verified successfully!',
                            'user_exists': True,
                            'action': 'redirect_to_dashboard',
                            'account_status': 'finished',
                            'next_action': 'login',
                            'email': user.email,
                            'user': user_data,
                            'api_token': api_token
                        }, status=status.HTTP_200_OK)
                    else:
                        # Incomplete profile - redirect to profile creation
                        return Response({
                            'success': True,
                            'message': 'Email verified! Please complete your profile.',
                            'user_exists': True,
                            'action': 'redirect_to_profile_creation',
                            'account_status': 'incomplete',
                            'next_action': 'complete_profile',
                            'user': user_data,
                            'api_token': api_token
                        }, status=status.HTTP_200_OK)
                else:
                    # New user - redirect to profile creation
                    # Ensure minimal user exists and create api token
                    api_token = None
                    try:
                        user, created = User.objects.get_or_create(email=email, defaults={'username': email})
                        api_token = secrets.token_hex(32)
                        user.api_token = api_token
                        user.save(update_fields=['api_token'])
                    except Exception as e:
                        print(f"❌ Failed to create user/generate api_token for {email}: {e}")

                    return Response({
                        'success': True,
                        'message': 'Email verified! Please complete your profile.',
                        'user_exists': False,
                        'action': 'redirect_to_profile_creation',
                        'account_status': 'new',
                        'next_action': 'create_profile',
                        'email': email,
                        'api_token': api_token
                    }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': message,
                    'attempts_remaining': otp.max_attempts - otp.attempts if otp.attempts < otp.max_attempts else 0
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Error verifying OTP. Please try again.',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'success': False,
        'message': 'Invalid data provided.',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_dashboard(request):
    """
    Simple dashboard endpoint
    """
    user = request.user
    user_data = UserSerializer(user).data
    
    return Response({
        'message': f'Welcome to your dashboard, {user.first_name}!',
        'user': user_data,
        'dashboard_data': {
            'profile_completion': 100,  # Could calculate this based on filled fields
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'member_since': user.created_at.isoformat(),
            'total_profiles': 1  # For now, just show 1
        }
    }, status=status.HTTP_200_OK)


# Individual Section Update Endpoints

@api_view(['PATCH'])
@permission_classes([AllowAny])
def update_basic_info(request):
    """Update basic information section"""
    email = request.data.get('email')
    if not email:
        return Response({'message': 'Email is required', 'status': 'error'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    print(f"DEBUG: Received data for basic info update: {dict(request.data)}")
    print(f"DEBUG: Email being searched: '{email}'")
    
    try:
        user = User.objects.get(email=email)
        print(f"DEBUG: Found user: {user.email} (ID: {user.id})")
        
        # Prepare data for serializer
        update_data = {}
        
        if 'firstName' in request.data and request.data['firstName']:
            print(f"DEBUG: Updating firstName: '{request.data['firstName']}'")
            update_data['first_name'] = request.data['firstName']
            
        if 'lastName' in request.data and request.data['lastName']:
            print(f"DEBUG: Updating lastName: '{request.data['lastName']}'")
            update_data['last_name'] = request.data['lastName']
            
        if 'phoneNumber' in request.data and request.data['phoneNumber']:
            print(f"DEBUG: Updating phoneNumber: '{request.data['phoneNumber']}'")
            update_data['phone_number'] = request.data['phoneNumber']
            
        if 'linkedinUrl' in request.data:
            linkedin_url = request.data['linkedinUrl'].strip() if request.data['linkedinUrl'] else ''
            print(f"DEBUG: Processing linkedinUrl: '{linkedin_url}'")
            update_data['linkedin_url'] = linkedin_url
                
        if 'website' in request.data:
            website = request.data['website'].strip() if request.data['website'] else ''
            print(f"DEBUG: Processing website: '{website}'")
            update_data['website'] = website
                
        if 'languages' in request.data:
            print(f"DEBUG: Updating languages: '{request.data['languages']}'")
            update_data['languages'] = request.data['languages']
            
        print(f"DEBUG: About to validate with serializer using data: {update_data}")
        
        # Use serializer for validation and saving
        serializer = UserUpdateSerializer(user, data=update_data, partial=True)
        if serializer.is_valid():
            print("DEBUG: Serializer is valid, saving user...")
            serializer.save()
            print("DEBUG: User saved successfully!")
        else:
            print(f"DEBUG: Serializer validation errors: {serializer.errors}")
            return Response({
                'message': 'Validation failed',
                'errors': serializer.errors,
                'status': 'error'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'message': 'Basic information updated successfully!',
            'status': 'success'
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        print(f"DEBUG: User not found with email: '{email}'")
        return Response({'message': 'User not found', 'status': 'error'}, 
                       status=status.HTTP_404_NOT_FOUND)
                # Section endpoints moved to users.views.profile_sections

                    
                    # Try to extract structured info
                    # Look for patterns like "Degree in Field from School (Years)"
                    import re
                    
                    # Pattern 1: "Degree in Field from School (Years)"
                    pattern1 = r'(.+?)\s+in\s+(.+?)\s+from\s+(.+?)\s*\(([^)]+)\)'
                    match = re.search(pattern1, line_without_number)
                    if match:
                        entry.update({
                            'degree': match.group(1).strip(),
                            'field': match.group(2).strip(),
                            'school': match.group(3).strip(),
                            'years': match.group(4).strip()
                        })
                    else:
                        # Pattern 2: "Degree from School (Years)" (for degrees without field)
                        pattern2 = r'(.+?)\s+from\s+(.+?)\s*\(([^)]+)\)'
                        match2 = re.search(pattern2, line_without_number)
                        if match2:
                            degree_part = match2.group(1).strip()
                            # Check if it's something like "Master of Business Administration"
                            if 'of' in degree_part:
                                entry.update({
                                    'degree': degree_part,
                                    'field': '',  # Field is part of the degree name
                                    'school': match2.group(2).strip(),
                                    'years': match2.group(3).strip()
                                })
                            else:
                                entry.update({
                                    'degree': degree_part,
                                    'field': '',
                                    'school': match2.group(2).strip(),
                                    'years': match2.group(3).strip()
                                })
                    
                    current_entry = entry
                elif current_entry and line:
                    # Add to description of current entry
                    if current_entry['description'] != current_entry.get('degree', '') + ' in ' + current_entry.get('field', ''):
                        current_entry['description'] += '\n' + line
                    else:
                        current_entry['description'] = line
            
            # Add the last entry
            if current_entry:
                education_entries.append(current_entry)
            
            # Replace the text with parsed structured data
            update_data['education'] = education_entries
            print(f"DEBUG: Converted to {len(education_entries)} structured education entries")
        
        # Handle special URL field validation for basic-info section
        if section_name == 'basic-info' and 'website' in update_data:
            website = update_data['website'].strip() if update_data['website'] else ''
            print(f"DEBUG: Processing website URL: '{website}'")
            if website == '':
                update_data['website'] = ''
            elif website.startswith('http'):
                update_data['website'] = website
            elif website and '.' in website:
                # Add http:// prefix if missing and it looks like a domain
                update_data['website'] = f'http://{website}'
                print(f"DEBUG: Fixed website URL to: '{update_data['website']}'")
            elif website:
                # Invalid website format - remove it from update data
                print(f"DEBUG: Invalid website format: '{website}' - removing from update")
                del update_data['website']
        
        # Update user with section data
        serializer = UserUpdateSerializer(user, data=update_data, partial=True)
        print(f"DEBUG: About to validate serializer with data: {update_data}")
        
        if serializer.is_valid():
            print("DEBUG: Serializer is valid, saving user...")
            updated_user = serializer.save()
            print("DEBUG: User saved successfully!")
            
            # Only update profile completion when not an autosave (autosave should not mark complete)
            is_autosave = False
            autosave_val = mapped_data.get('autosave')
            if autosave_val is not None:
                try:
                    if isinstance(autosave_val, str):
                        is_autosave = autosave_val.lower() in ['true', '1', 'yes', 'on']
                    else:
                        is_autosave = bool(autosave_val)
                except Exception:
                    is_autosave = False

            if not is_autosave:
                # Force check and update profile completion status
                profile_was_completed = updated_user.profile_completed
                force_profile_complete = updated_user.mark_profile_complete()

                if not profile_was_completed and force_profile_complete:
                    print(f"DEBUG: Profile completion status updated to True for user {updated_user.email}")
            else:
                print(f"DEBUG: Autosave detected for {email}; skipping profile completion check")
            
            return Response({
                'status': 'success',
                'message': f'{section_name.replace("-", " ").title()} updated successfully!',
                'user': UserSerializer(updated_user).data
            }, status=status.HTTP_200_OK)
        else:
            print(f"DEBUG: Serializer validation failed: {serializer.errors}")
            return Response({
                'status': 'error',
                'message': 'Validation failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        import traceback
        print(f"DEBUG: Exception in update_profile_section: {str(e)}")
        print(f"DEBUG: Full traceback: {traceback.format_exc()}")
        return Response({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def ai_profile_extraction(request):
    # Implementation moved to `users.views.ai.ai_profile_extraction`.
    # See users/views/ai.py for the implementation.
    from .views.ai import ai_profile_extraction as _impl
    return _impl(request)


# AI endpoints moved to users.views.ai

@api_view(['PATCH'])
@permission_classes([AllowAny])
def update_location(request):
    print("DEBUG: update_location called with data:", request.data)
    """
    Update location section
    """
    email = request.data.get('email')
    if not email:
        return Response({'status': 'error', 'message': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'status': 'error', 'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    if 'country' in request.data:
        user.country = request.data['country']
    if 'state' in request.data:
        user.state = request.data['state']
    if 'city' in request.data:
        user.city = request.data['city']

    user.save()

    return Response({'status': 'success', 'message': 'Location updated successfully'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def multi_source_extraction(request):
    """
    Multi-source AI-powered profile extraction endpoint
    Accepts resume, buyer profile files, and LinkedIn URL for comprehensive AI processing
    """
    # Delegate to implementation in users.views.ai
    from .views.ai import multi_source_extraction as _impl
    return _impl(request)

@api_view(['POST'])
@permission_classes([AllowAny])
def save_professional_experience_data(request):
    """
    Endpoint to save professional experience data directly to the database
    """
    try:
        email = request.data.get('email')
        experience_data = request.data.get('experience_data')
        
        if not email:
            return Response({
                'status': 'error',
                'message': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not experience_data:
            return Response({
                'status': 'error',
                'message': 'Experience data is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        print(f"DEBUG: Saving professional experience for {email}")
        print(f"DEBUG: Experience data type: {type(experience_data)}")
        
        # Get or create user
        try:
            user = User.objects.get(email=email)
            print(f"DEBUG: Found existing user: {user.email}")
        except User.DoesNotExist:
            # Create new user if doesn't exist
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'is_active': True,
                    'profile_completed': False
                }
            )
            print(f"DEBUG: {'Created' if created else 'Retrieved'} user: {user.email}")
        
        # Parse and save experience data
        if isinstance(experience_data, list):
            # Already structured data
            user.professional_experience = experience_data
            print(f"DEBUG: Saved {len(experience_data)} structured experiences")
        elif isinstance(experience_data, str):
            # Parse text data into structured format
            experiences = []
            lines = experience_data.strip().split('\n')
            
            current_experience = None
            for line in lines:
                line = line.strip()
                if not line:
                    if current_experience:
                        experiences.append(current_experience)
                        current_experience = None
                    continue
                
                # Check if this is a new experience (starts with number)
                if line.split('.')[0].strip().isdigit():
                    if current_experience:
                        experiences.append(current_experience)
                    
                    # Parse new experience
                    line_without_number = '.'.join(line.split('.')[1:]).strip()
                    
                    # Extract title, company, and duration
                    experience = {
                        'id': len(experiences) + 1,
                        'title': '',
                        'company': '',
                        'duration': '',
                        'description': line_without_number
                    }
                    
                    # Try to parse structure
                    if ' at ' in line_without_number:
                        parts = line_without_number.split(' at ', 1)
                        experience['title'] = parts[0].strip()
                        remaining = parts[1].strip()
                        
                        # Look for duration pattern
                        import re
                        date_pattern = r'\(([^)]+)\)'
                        date_match = re.search(date_pattern, remaining)
                        
                        if date_match:
                            experience['duration'] = date_match.group(1)
                            experience['company'] = remaining[:date_match.start()].strip()
                            # Description is everything after the date
                            desc_start = date_match.end()
                            if desc_start < len(remaining):
                                desc_text = remaining[desc_start:].strip()
                                if desc_text:
                                    experience['description'] = desc_text
                        else:
                            experience['company'] = remaining
                    
                    current_experience = experience
                    
                elif current_experience and line:
                    # Add to description of current experience
                    if current_experience['description'] and current_experience['description'] != (current_experience['title'] + ' at ' + current_experience['company']):
                        current_experience['description'] += '\n' + line
                    else:
                        current_experience['description'] = line
            
            # Add the last experience
            if current_experience:
                experiences.append(current_experience)
            
            user.professional_experience = experiences
            print(f"DEBUG: Parsed and saved {len(experiences)} experiences from text")
        
        user.save()
        
        return Response({
            'status': 'success',
            'message': f'Successfully saved {len(user.professional_experience)} professional experiences',
            'experiences_count': len(user.professional_experience),
            'experiences': user.professional_experience
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"DEBUG: Error saving professional experience: {str(e)}")
        import traceback
        print(f"DEBUG: Full traceback: {traceback.format_exc()}")
        return Response({
            'status': 'error',
            'message': f'Failed to save professional experience: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_questions_list(request):
    """
    Get the list of active questions for the questionnaire
    """
    try:
        from .models import Question
        
        questions = Question.objects.filter(is_active=True).order_by('order')
        
        questions_data = []
        for question in questions:
            question_data = {
                'id': question.id,
                'text': question.text,
                'type': question.question_type,
                'required': question.required,
                'placeholder': question.placeholder or '',
                'order': question.order
            }
            
            if question.options:
                question_data['options'] = question.options
                
            questions_data.append(question_data)
        
        return Response({
            'status': 'success',
            'questions': questions_data,
            'total_questions': len(questions_data)
        })
        
    except Exception as e:
        print(f"ERROR: Failed to fetch questions: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Failed to fetch questions: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def test_questionnaire_answers(request):
    """
    Test endpoint to receive questionnaire answers in JSON format
    """
    try:
        # Get the answers from request data
        answers = request.data.get('answers', {})
        
        if not answers:
            return Response({
                'status': 'error',
                'message': 'No answers provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        print(f"DEBUG: Received questionnaire answers: {answers}")
        
        # Validate answers format
        if not isinstance(answers, dict):
            return Response({
                'status': 'error',
                'message': 'Answers must be provided as a JSON object'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Log the received answers for testing
        print("=== QUESTIONNAIRE ANSWERS RECEIVED ===")
        for question_id, answer in answers.items():
            print(f"  {question_id}: {answer}")
        print("=== END QUESTIONNAIRE ANSWERS ===")
        
        # You can add validation against actual questions here
        from .models import Question
        valid_question_ids = set(Question.objects.filter(is_active=True).values_list('id', flat=True))
        
        # Check which questions were answered
        answered_questions = []
        unknown_questions = []
        
        for question_id in answers.keys():
            if question_id in valid_question_ids:
                answered_questions.append(question_id)
            else:
                unknown_questions.append(question_id)
        
        response_data = {
            'status': 'success',
            'message': 'Questionnaire answers received successfully',
            'answers_received': answers,
            'summary': {
                'total_answers': len(answers),
                'valid_questions_answered': len(answered_questions),
                'unknown_questions': unknown_questions if unknown_questions else None
            }
        }
        
        return Response(response_data)
        
    except Exception as e:
        print(f"ERROR: Failed to process questionnaire answers: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Failed to process questionnaire answers: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Signed Links Views
from .models import Signed_links, OTPVerification
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

@api_view(['POST'])
@permission_classes([AllowAny])  # You might want to restrict this to admin users later
def create_signed_link(request):
    """
    Create a signed link and send invitation email
    """
    try:
        email = request.data.get('email')
        if not email:
            return Response({
                'status': 'error',
                'message': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if there's already a valid link for this email
        existing_link = Signed_links.objects.filter(
            email=email,
            used=False,
            expires_at__gt=timezone.now()
        ).first()
        
        if existing_link:
            token = existing_link.token
        else:
            # Create new signed link
            signed_link = Signed_links.objects.create(email=email)
            token = signed_link.token
        
        # Create the invitation URL (default to production frontend)
        frontend_url = request.data.get('frontend_url', 'https://www.searcherlist.com')
        invitation_url = f"{frontend_url}/profile-upload?token={token}&email={email}"
        
        # Send invitation email
        try:
            send_mail(
                subject='You have been invited to SearcherList',
                message=f'''
You have been invited to join SearcherList!

Please click the link below to access your profile creation page:
{invitation_url}

This link will expire in 24 hours.

Best regards,
The SearcherList Team
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            
            return Response({
                'status': 'success',
                'message': 'Invitation sent successfully',
                'token': str(token),
                'invitation_url': invitation_url
            })
            
        except Exception as email_error:
            return Response({
                'status': 'warning',
                'message': 'Link created but email could not be sent',
                'token': str(token),
                'invitation_url': invitation_url,
                'email_error': str(email_error)
            })
            
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Failed to create signed link: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def validate_signed_link(request):
    """
    Validate a signed link token and send OTP to email
    """
    try:
        token = request.data.get('token')
        email = request.data.get('email')
        
        print(f"🔍 BACKEND DEBUG - Validating signed link:")
        print(f"Token: {token}")
        print(f"Email: {email}")
        
        if not token or not email:
            print("❌ Missing token or email")
            return Response({
                'status': 'error',
                'message': 'Token and email are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # STRICT CHECK: Token AND email must match exactly
            signed_link = Signed_links.objects.get(token=token, email=email)
            print(f"✅ Found signed link: {signed_link}")
            print(f"Used: {signed_link.used}, Expires: {signed_link.expires_at}")
            
            # Additional security: Check if this exact combination exists
            if signed_link.email != email or str(signed_link.token) != token:
                print("❌ Token/email mismatch detected")
                return Response({
                    'status': 'error',
                    'message': 'This email has not been invited to access the application. Please contact support.',
                    'error_type': 'not_invited'
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Signed_links.DoesNotExist:
            print("❌ Signed link not found - email not invited")
            return Response({
                'status': 'error',
                'message': 'This email has not been invited to access the application. Please contact support.',
                'error_type': 'not_invited'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if not signed_link.is_valid():
            reason = "already used" if signed_link.used else "expired"
            print(f"❌ Link is {reason}")
            return Response({
                'status': 'error',
                'message': f'Invitation link is {reason}. Please contact support for a new invitation.',
                'error_type': 'expired_or_used'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create and send OTP
        otp_verification = OTPVerification.objects.create(
            email=email,
            signed_link=signed_link
        )
        
        # Send OTP email
        try:
            send_mail(
                subject='Your Access Code - Searcher Platform',
                message=f'Your access code is: {otp_verification.otp_code}\n\nThis code will expire in 10 minutes.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=f'''
                <html>
                <body>
                    <h2>Your Access Code</h2>
                    <p>Your access code for the Searcher Platform is:</p>
                    <h1 style="color: #007bff; font-size: 36px; text-align: center; margin: 20px 0;">{otp_verification.otp_code}</h1>
                    <p>This code will expire in 10 minutes.</p>
                    <p>If you didn't request this code, please ignore this email.</p>
                </body>
                </html>
                ''',
                fail_silently=False,
            )
            print(f"📧 OTP sent to {email}: {otp_verification.otp_code}")
        except Exception as e:
            print(f"❌ Failed to send OTP email: {e}")
            return Response({
                'status': 'error',
                'message': 'Failed to send access code. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'status': 'success',
            'message': 'Access code sent to your email',
            'email': email,
            'requires_otp': True
        })
        
    except Exception as e:
        print(f"💥 BACKEND ERROR: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Failed to validate link: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    """
    Verify OTP code and grant access
    """
    try:
        email = request.data.get('email')
        otp_code = request.data.get('otp_code')
        
        print(f"🔍 BACKEND DEBUG - Verifying OTP:")
        print(f"Email: {email}")
        print(f"OTP Code: {otp_code}")
        
        if not email or not otp_code:
            print("❌ Missing email or OTP code")
            return Response({
                'status': 'error',
                'message': 'Email and OTP code are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get the most recent valid OTP for this email
            otp_verification = OTPVerification.objects.filter(
                email=email,
                otp_code=otp_code,
                used=False
            ).order_by('-created_at').first()
            
            if not otp_verification:
                print("❌ OTP not found or already used")
                return Response({
                    'status': 'error',
                    'message': 'Invalid or expired access code'
                }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            return Response({
                'status': 'error',
                'message': 'Invalid access code'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if not otp_verification.is_valid():
            reason = "already used" if otp_verification.used else "expired"
            print(f"❌ OTP is {reason}")
            return Response({
                'status': 'error',
                'message': f'Access code is {reason}. Please request a new invitation.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Mark OTP as used
        otp_verification.mark_as_used()
        
        # Mark the signed link as used (one-time access)
        otp_verification.signed_link.mark_as_used()
        
        print(f"✅ OTP verified successfully for {email}")
        # Create or find the user and generate an API token for bearer auth
        api_token = None
        try:
            user, created = User.objects.get_or_create(email=email, defaults={'username': email})
            try:
                api_token = secrets.token_hex(32)
                user.api_token = api_token
                user.save(update_fields=['api_token'])
            except Exception as e:
                print(f"❌ Failed to generate/save api_token for {email}: {e}")
        except Exception as e:
            print(f"❌ Failed to get/create user for signed link verification {email}: {e}")

        return Response({
            'status': 'success',
            'message': 'Access granted',
            'email': email,
            'access_granted': True,
            'api_token': api_token
        })
        
    except Exception as e:
        print(f"💥 BACKEND ERROR: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

