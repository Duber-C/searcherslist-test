
from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from django.conf import settings
from .serializers import (
    UserRegistrationSerializer, UserSerializer, UserUpdateSerializer,
    SendOTPSerializer, VerifyOTPSerializer, OTPSerializer
)
from .otp_models import OTP
from .email_service import EmailService
import sys
import os

# Add the ai_profile_creation directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ai_profile_creation'))

User = get_user_model()


# Public profile view by email (for preview/public-profile page)
@api_view(['GET'])
def public_profile_view(request, email):
    """
    Get public profile data by email (for preview/public-profile page)
    """
    try:
        print(f"🔍 Fetching public profile for email: {email}")
        user = User.objects.get(email=email)
        # You can filter which fields to expose publicly here
        public_data = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'bio': user.bio,
            'background': user.background,
            'linkedin_url': user.linkedin_url,
            'education': user.education,
            'professional_experience': user.professional_experience,
            'skills': user.skills,
            'company': user.company,
            'current_role': user.current_role,
            'profile_completed': user.profile_completed,
        }
        return Response({'success': True, 'data': public_data})
    except User.DoesNotExist:
        return Response({'success': False, 'message': 'User not found'}, status=404)
    
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
            }
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'success': True,
            'user_exists': False,
            'profile_completed': False,
            'data': {}
        }, status=status.HTTP_200_OK)



@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def publish_profile(request):
    """
    Publish the authenticated user's profile. Marks `published=True`.
    If the profile is not marked completed, mark it completed as well.
    """
    try:
        user = request.user
        if not user:
            return Response({'success': False, 'message': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        # Set published flag
        user.published = True

        # If profile wasn't completed, mark it completed now
        if not user.profile_completed:
            user.profile_completed = True
            user.save(update_fields=['published', 'profile_completed'])
        else:
            user.save(update_fields=['published'])

        return Response({
            'success': True,
            'message': 'Profile published successfully',
            'published': user.published,
            'profile_completed': user.profile_completed
        }, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"❌ Error publishing profile: {e}")
        return Response({'success': False, 'message': 'Error publishing profile', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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

        return Response({'success': True, 'message': 'Profile published (dev)', 'published': user.published}, status=status.HTTP_200_OK)

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
        
        # Determine user status
        try:
            user = User.objects.get(email=email)
            if user.profile_completed:
                account_status = 'finished'
                next_action = 'dashboard'
            else:
                account_status = 'incomplete'
                next_action = 'complete_profile'
        except User.DoesNotExist:
            account_status = 'new'
            next_action = 'create_profile'
        
        return Response({
            'success': True,
            'message': 'OTP verified successfully!',
            'email': email,
            'account_status': account_status,
            'next_action': next_action,
            'user_exists': account_status != 'new'
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
                            'user': user_data
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
                            'user': user_data
                        }, status=status.HTTP_200_OK)
                else:
                    # New user - redirect to profile creation
                    return Response({
                        'success': True,
                        'message': 'Email verified! Please complete your profile.',
                        'user_exists': False,
                        'action': 'redirect_to_profile_creation',
                        'account_status': 'new',
                        'next_action': 'create_profile',
                        'email': email
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
    except Exception as e:
        import traceback
        print(f"DEBUG: Error in update_basic_info: {str(e)}")
        print(f"DEBUG: Full traceback: {traceback.format_exc()}")
        return Response({'message': f'Update failed: {str(e)}', 'status': 'error'}, 
                       status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
@permission_classes([AllowAny])
def update_location(request):
    """Update location information section"""
    email = request.data.get('email')
    if not email:
        return Response({'message': 'Email is required', 'status': 'error'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    print(f"DEBUG: Location update - Received data: {dict(request.data)}")
    
    try:
        user = User.objects.get(email=email)
        
        # Update location fields
        if 'country' in request.data:
            user.country = request.data['country']
        if 'state' in request.data:
            user.state = request.data['state']
        if 'city' in request.data:
            user.city = request.data['city']
            
        user.save()
        
        return Response({
            'message': 'Location updated successfully!',
            'status': 'success'
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({'message': 'User not found', 'status': 'error'}, 
                       status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'message': str(e), 'status': 'error'}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
@permission_classes([AllowAny])
def update_target_statement(request):
    """Update target statement section"""
    email = request.data.get('email')
    if not email:
        return Response({'message': 'Email is required', 'status': 'error'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    print(f"DEBUG: Target statement update - Received data: {dict(request.data)}")
    
    try:
        user = User.objects.get(email=email)
        
        # Update target statement fields
        if 'background' in request.data:
            user.background = request.data['background']
            
        user.save()
        
        return Response({
            'message': 'Target statement updated successfully!',
            'status': 'success'
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({'message': 'User not found', 'status': 'error'}, 
                       status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'message': str(e), 'status': 'error'}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
@permission_classes([AllowAny])
def update_value_proposition(request):
    """Update value proposition section"""
    email = request.data.get('email')
    if not email:
        return Response({'message': 'Email is required', 'status': 'error'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    print(f"DEBUG: Value proposition update - Received data: {dict(request.data)}")
    
    try:
        user = User.objects.get(email=email)
        
        # Update value proposition fields
        if 'valueProposition' in request.data:
            user.value_proposition = request.data['valueProposition']
            
        user.save()
        
        return Response({
            'message': 'Value proposition updated successfully!',
            'status': 'success'
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({'message': 'User not found', 'status': 'error'}, 
                       status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'message': str(e), 'status': 'error'}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
@permission_classes([AllowAny])
def update_expertise(request):
    """Update areas of expertise section"""
    email = request.data.get('email')
    if not email:
        return Response({'message': 'Email is required', 'status': 'error'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    print(f"DEBUG: Expertise update - Received data: {dict(request.data)}")
    
    try:
        user = User.objects.get(email=email)
        
        # Update expertise fields
        if 'areasOfExpertise' in request.data:
            user.areas_of_expertise = request.data['areasOfExpertise']
        if 'skills' in request.data:
            user.skills = request.data['skills']
            
        user.save()
        
        return Response({
            'message': 'Areas of expertise updated successfully!',
            'status': 'success'
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({'message': 'User not found', 'status': 'error'}, 
                       status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'message': str(e), 'status': 'error'}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
@permission_classes([AllowAny])
def update_professional_experience(request):
    """Update professional experience section"""
    email = request.data.get('email')
    if not email:
        return Response({'message': 'Email is required', 'status': 'error'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    print(f"DEBUG: Professional experience update - Received data: {dict(request.data)}")
    print(f"DEBUG: Request data type: {type(request.data)}")
    
    try:
        user = User.objects.get(email=email)
        print(f"DEBUG: Found user: {user.email}")
        print(f"DEBUG: Current values before update:")
        print(f"  - current_role: '{user.current_role}'")
        print(f"  - company: '{user.company}'") 
        print(f"  - years_experience: '{user.years_experience}'")
        print(f"  - bio: '{user.bio}'")
        
        # Update professional experience fields
        if 'currentRole' in request.data:
            new_value = request.data['currentRole']
            print(f"DEBUG: Updating currentRole from '{user.current_role}' to '{new_value}'")
            user.current_role = new_value
        if 'company' in request.data:
            new_value = request.data['company']
            print(f"DEBUG: Updating company from '{user.company}' to '{new_value}'")
            user.company = new_value
        if 'yearsExperience' in request.data:
            new_value = request.data['yearsExperience']
            print(f"DEBUG: Updating yearsExperience from '{user.years_experience}' to '{new_value}'")
            user.years_experience = new_value
        if 'bio' in request.data:
            new_value = request.data['bio']
            print(f"DEBUG: Updating bio from '{user.bio}' to '{new_value}'")
            user.bio = new_value
        if 'investmentExperience' in request.data:
            user.investment_experience = request.data['investmentExperience']
        if 'dealSizePreference' in request.data:
            user.deal_size_preference = request.data['dealSizePreference']
        if 'industryFocus' in request.data:
            user.industry_focus = request.data['industryFocus']
        if 'geographicFocus' in request.data:
            user.geographic_focus = request.data['geographicFocus']
        
        # Handle professional_experience JSONField (structured data)
        if 'professionalExperience' in request.data:
            prof_exp_data = request.data['professionalExperience']
            print(f"DEBUG: Received professionalExperience data: {prof_exp_data}")
            
            # Convert text to structured data if needed
            if isinstance(prof_exp_data, str) and prof_exp_data.strip():
                # Parse text into structured format
                experiences = []
                lines = prof_exp_data.split('\n\n')  # Split by double newlines
                
                for i, line in enumerate(lines):
                    if line.strip():
                        # Remove numbering at start if present
                        clean_line = line.strip()
                        if clean_line.split('.')[0].strip().isdigit():
                            clean_line = '.'.join(clean_line.split('.')[1:]).strip()
                        
                        # Try to parse the line into company, title, duration, description
                        experience_entry = {
                            'id': i + 1,
                            'company': '',
                            'title': '',
                            'duration': '',
                            'description': clean_line
                        }
                        
                        # Basic parsing - look for common patterns
                        if ' at ' in clean_line:
                            parts = clean_line.split(' at ', 1)
                            experience_entry['title'] = parts[0].strip()
                            remaining = parts[1]
                            
                            # Look for date pattern (YYYY-MM-DD or similar)
                            import re
                            date_pattern = r'\((.*?)\)'
                            date_match = re.search(date_pattern, remaining)
                            if date_match:
                                experience_entry['duration'] = date_match.group(1)
                                experience_entry['company'] = remaining[:date_match.start()].strip()
                                # Description is everything after the date pattern
                                desc_start = date_match.end()
                                if desc_start < len(remaining):
                                    experience_entry['description'] = remaining[desc_start:].strip()
                            else:
                                experience_entry['company'] = remaining.strip()
                        
                        experiences.append(experience_entry)
                
                user.professional_experience = experiences
                print(f"DEBUG: Converted to structured data: {experiences}")
            
            elif isinstance(prof_exp_data, list):
                # Already structured data
                user.professional_experience = prof_exp_data
                print(f"DEBUG: Using structured data: {prof_exp_data}")
        
        # Handle professional_experience directly (for backend field name)
        elif 'professional_experience' in request.data:
            prof_exp_data = request.data['professional_experience']
            print(f"DEBUG: Received professional_experience (backend field) data: {prof_exp_data}")
            
            if isinstance(prof_exp_data, (list, dict)):
                user.professional_experience = prof_exp_data
            elif isinstance(prof_exp_data, str) and prof_exp_data.strip():
                # Try to parse as JSON first
                try:
                    import json
                    user.professional_experience = json.loads(prof_exp_data)
                    print(f"DEBUG: Parsed JSON: {user.professional_experience}")
                except json.JSONDecodeError:
                    # Store as single entry with the full text as description
                    user.professional_experience = [{
                        'id': 1,
                        'company': '',
                        'title': '',
                        'duration': '',
                        'description': prof_exp_data
                    }]
                    print(f"DEBUG: Stored as single entry: {user.professional_experience}")
        
        print(f"DEBUG: About to save user...")
        user.save()
        print(f"DEBUG: User saved successfully!")
        
        print(f"DEBUG: Values after save:")
        print(f"  - current_role: '{user.current_role}'")
        print(f"  - company: '{user.company}'") 
        print(f"  - years_experience: '{user.years_experience}'")
        print(f"  - bio: '{user.bio}'")
        
        return Response({
            'message': 'Professional experience updated successfully!',
            'status': 'success'
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({'message': 'User not found', 'status': 'error'}, 
                       status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'message': str(e), 'status': 'error'}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
@permission_classes([AllowAny])
def update_education(request):
    """Update education and certifications section"""
    email = request.data.get('email')
    if not email:
        return Response({'message': 'Email is required', 'status': 'error'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    print(f"DEBUG: Education update - Received data: {dict(request.data)}")
    
    try:
        user = User.objects.get(email=email)
        
        # Update education fields
        if 'education' in request.data:
            edu_data = request.data['education']
            print(f"DEBUG: Received education data: {edu_data}")
            
            # Handle different data formats
            if isinstance(edu_data, str) and edu_data.strip():
                try:
                    import json
                    # Try to parse as JSON first
                    user.education = json.loads(edu_data)
                    print(f"DEBUG: Parsed education JSON: {user.education}")
                except json.JSONDecodeError:
                    # If not JSON, try to parse as text
                    education_entries = []
                    lines = edu_data.strip().split('\n')
                    
                    current_entry = None
                    for i, line in enumerate(lines):
                        line = line.strip()
                        if not line:
                            if current_entry:
                                education_entries.append(current_entry)
                                current_entry = None
                            continue
                        
                        # Check if this is a new education entry
                        if line.split('.')[0].strip().isdigit():
                            if current_entry:
                                education_entries.append(current_entry)
                            
                            # Parse education entry
                            line_without_number = '.'.join(line.split('.')[1:]).strip()
                            
                            entry = {
                                'id': len(education_entries) + 1,
                                'school': '',
                                'degree': '',
                                'field': '',
                                'years': '',
                                'description': line_without_number
                            }
                            
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
                    
                    user.education = education_entries
                    print(f"DEBUG: Parsed education text to {len(education_entries)} entries")
            
            elif isinstance(edu_data, list):
                # Already structured data
                user.education = edu_data
                print(f"DEBUG: Using structured education data: {len(edu_data)} entries")
        
        if 'certifications' in request.data:
            user.certifications = request.data['certifications']
        if 'achievements' in request.data:
            user.achievements = request.data['achievements']
            
        user.save()
        
        return Response({
            'message': 'Education and certifications updated successfully!',
            'status': 'success'
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({'message': 'User not found', 'status': 'error'}, 
                       status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'message': str(e), 'status': 'error'}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
@permission_classes([AllowAny])
def update_profile_section(request, section_name):
    """
    Update individual profile sections
    """
    try:
        print(f"DEBUG: update_profile_section called for section: {section_name}")
        print(f"DEBUG: request.data type: {type(request.data)}")
        print(f"DEBUG: request.data: {request.data}")
        
        # Handle both JSON and form data
        if hasattr(request.data, 'dict'):
            # QueryDict from form data - convert to regular dict
            data_dict = dict(request.data)
            # Extract single values from lists (QueryDict stores values as lists)
            processed_data = {}
            for key, value_list in data_dict.items():
                processed_data[key] = value_list[0] if isinstance(value_list, list) and value_list else value_list
            print(f"DEBUG: processed form data: {processed_data}")
        else:
            # Regular dict from JSON data
            processed_data = dict(request.data)
            print(f"DEBUG: using JSON data: {processed_data}")
        
        # Map frontend fields to backend fields
        mapped_data = map_frontend_fields(processed_data)
        print(f"DEBUG: mapped_data: {mapped_data}")
        
        email = mapped_data.get('email')
        if not email:
            print("DEBUG: No email found in data")
            return Response({
                'status': 'error',
                'message': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        print(f"DEBUG: Looking for user with email: {email}")
        
        # Get or create user
        try:
            user = User.objects.get(email=email)
            print(f"DEBUG: Found existing user: {user.email} (ID: {user.id})")
        except User.DoesNotExist:
            print(f"DEBUG: User not found with email: {email}, creating new user...")
            
            # Extract name information if available
            first_name = mapped_data.get('first_name', '')
            last_name = mapped_data.get('last_name', '')
            
            # Use get_or_create to prevent race conditions
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,  # Use email as username
                    'first_name': first_name,
                    'last_name': last_name,
                    'is_active': True,
                    'profile_completed': False  # Using the correct field name
                }
            )
            
            if created:
                print(f"DEBUG: Created new user: {user.email} (ID: {user.id}) - {first_name} {last_name}")
                
                # Set a secure random password (user will use OTP for login)
                from django.contrib.auth.hashers import make_password
                import secrets
                temp_password = secrets.token_urlsafe(16)
                user.password = make_password(temp_password)
                user.save()
                
                print(f"DEBUG: New user setup complete for {email}")
            else:
                print(f"DEBUG: User was created by another request: {user.email} (ID: {user.id})")
        
        # Define section field mappings (using backend field names)
        section_mappings = {
            'basic-info': ['first_name', 'last_name', 'phone_number', 'linkedin_url', 'website', 'languages'],
            'location': ['country', 'state', 'city'],
            'target-statement': ['background'],
            'value-proposition': ['value_proposition'],
            'expertise': ['areas_of_expertise', 'skills', 'investment_experience', 'deal_size_preference', 'geographic_focus', 'industry_focus', 'value_proposition'],
            'professional-experience': ['current_role', 'company', 'years_experience', 'bio', 'professional_experience'],
            'experience': ['current_role', 'company', 'years_experience', 'bio', 'professional_experience'],  # Alias for professional-experience
            'education': ['education', 'certifications', 'achievements'],
            'certifications': ['certifications', 'achievements']  # Alias for certifications part of education
        }
        
        if section_name not in section_mappings:
            print(f"DEBUG: Invalid section name: {section_name}")
            return Response({
                'status': 'error',
                'message': f'Invalid section: {section_name}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update only the fields for this section
        section_fields = section_mappings[section_name]
        update_data = {field: mapped_data.get(field) for field in section_fields if field in mapped_data}
        print(f"DEBUG: update_data for {section_name}: {update_data}")
        
        # Special handling for professional_experience field if it's in the update
        if 'professional_experience' in update_data and isinstance(update_data['professional_experience'], str):
            prof_exp_text = update_data['professional_experience']
            print(f"DEBUG: Processing professional_experience text: {prof_exp_text[:100]}...")
            
            # Parse text into structured format (same logic as direct endpoint)
            experiences = []
            lines = prof_exp_text.strip().split('\n')
            
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
            
            # Replace the text with parsed structured data
            update_data['professional_experience'] = experiences
            print(f"DEBUG: Converted to {len(experiences)} structured experiences")
        
        # Special handling for education field if it's in the update
        if 'education' in update_data and isinstance(update_data['education'], str):
            edu_text = update_data['education']
            print(f"DEBUG: Processing education text: {edu_text[:100]}...")
            
            # Parse text into structured format (same logic as dedicated endpoint)
            education_entries = []
            lines = edu_text.strip().split('\n')
            
            current_entry = None
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    if current_entry:
                        education_entries.append(current_entry)
                        current_entry = None
                    continue
                
                # Check if this is a new education entry
                if line.split('.')[0].strip().isdigit():
                    if current_entry:
                        education_entries.append(current_entry)
                    
                    # Parse education entry
                    line_without_number = '.'.join(line.split('.')[1:]).strip()
                    
                    entry = {
                        'id': len(education_entries) + 1,
                        'school': '',
                        'degree': '',
                        'field': '',
                        'years': '',
                        'description': line_without_number
                    }
                    
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
    """
    AI-powered profile extraction endpoint
    Accepts file upload for AI processing and stores file content
    """
    try:
        # Import the AI profile creation functions
        from chatGpt import extract_profile_from_text, extract_text_from_docx, extract_profile_from_multiple_sources
        import tempfile
        import os
        
        print("DEBUG: Starting AI profile extraction...")
        print(f"DEBUG: Request FILES: {request.FILES.keys()}")
        print(f"DEBUG: Request data: {request.data.keys()}")
        
        text_to_process = None
        file_type = None  # Track which type of file was uploaded
        user_email = request.data.get('email')  # Get user email at top level
        
        # Check if we should process an existing uploaded file
        if request.data.get('process_existing_file'):
            file_type = request.data.get('file_type', 'resume')
            
            if not user_email:
                return Response({
                    'status': 'error',
                    'message': 'Email is required when processing existing file'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            print(f"DEBUG: Processing existing {file_type} file for user: {user_email}")
            
            # Get the user to access their files
            try:
                user = User.objects.get(email=user_email)
            except User.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'User not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Get the file object based on file type
            file_obj = None
            if file_type == 'resume' and user.resume:
                file_obj = user.resume
            elif file_type == 'buyer_profile' and user.buyer_profile:
                file_obj = user.buyer_profile
            
            if not file_obj:
                return Response({
                    'status': 'error',
                    'message': f'No {file_type} file found for user'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check file extension
            file_path = file_obj.path
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension not in ['.pdf', '.doc', '.docx']:
                return Response({
                    'status': 'error',
                    'message': 'Unsupported file format. Only PDF, DOC, and DOCX files are supported.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Extract text from the existing file
            try:
                print(f"DEBUG: File path to extract from: {file_path}")
                print(f"DEBUG: File exists: {os.path.exists(file_path)}")
                print(f"DEBUG: File size: {os.path.getsize(file_path) if os.path.exists(file_path) else 'N/A'} bytes")
                print(f"DEBUG: File extension: {file_extension}")
                
                if file_extension == '.pdf':
                    return Response({
                        'status': 'error',
                        'message': 'PDF processing not yet implemented. Please use DOC or DOCX files.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    # For DOC/DOCX files
                    print(f"DEBUG: About to call extract_text_from_docx...")
                    text_to_process = extract_text_from_docx(file_path)
                    print(f"DEBUG: Successfully extracted text from existing file, length: {len(text_to_process)} characters")
                    if len(text_to_process) < 100:
                        print(f"DEBUG: Short text extracted: '{text_to_process[:200]}...'")
                    else:
                        print(f"DEBUG: Text preview: '{text_to_process[:200]}...'")
            except Exception as e:
                print(f"DEBUG: Error extracting text from existing file: {str(e)}")
                print(f"DEBUG: Exception type: {type(e)}")
                import traceback
                print(f"DEBUG: Full traceback: {traceback.format_exc()}")
                return Response({
                    'status': 'error',
                    'message': f'Failed to extract text from existing file: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Check if a file was uploaded
        elif 'file' in request.FILES:
            uploaded_file = request.FILES['file']
            print(f"DEBUG: Processing uploaded file: {uploaded_file.name}")
            
            # Determine file type based on form field name or file name
            file_name = uploaded_file.name.lower()
            if 'resume' in file_name or 'cv' in file_name:
                file_type = 'resume'
            elif 'buyer' in file_name or 'profile' in file_name:
                file_type = 'buyer_profile'
            else:
                file_type = 'resume'  # Default to resume
            
            print(f"DEBUG: Detected file type: {file_type}")
            
            # Save the uploaded file temporarily
            # Create a temporary file with the same extension
            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            
            if file_extension not in ['.pdf', '.doc', '.docx']:
                return Response({
                    'status': 'error',
                    'message': 'Unsupported file format. Please upload PDF, DOC, or DOCX files only.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                # Write uploaded file content to temp file
                for chunk in uploaded_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            try:
                # Extract text from the document
                if file_extension == '.pdf':
                    # For PDF, we'll need to add PDF text extraction
                    return Response({
                        'status': 'error',
                        'message': 'PDF processing not yet implemented. Please use DOC or DOCX files.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    # For DOC/DOCX files
                    text_to_process = extract_text_from_docx(temp_file_path)
                    print(f"DEBUG: Extracted text length: {len(text_to_process)} characters")
            
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
        
        # Check if text was provided directly
        elif 'text' in request.data:
            text_to_process = request.data['text']
            print(f"DEBUG: Processing provided text, length: {len(text_to_process)} characters")
        
        # Use sample text if no input provided (for testing)
        else:
            sample_text = """
            John Smith
            Senior Investment Analyst
            ABC Capital Partners
            
            Professional Summary:
            Experienced investment professional with 8+ years in private equity and venture capital.
            Strong background in technology sector investments and portfolio management.
            
            Experience:
            - Senior Investment Analyst at ABC Capital Partners (2020-Present)
            - Investment Associate at XYZ Ventures (2016-2020)
            - Financial Analyst at DEF Corporation (2014-2016)
            
            Education:
            - MBA Finance, Harvard Business School (2014)
            - Bachelor of Science in Economics, Stanford University (2012)
            
            Skills:
            - Financial modeling and valuation
            - Due diligence and market analysis
            - Portfolio management
            - Deal sourcing and execution
            
            Location: New York, NY, USA
            LinkedIn: linkedin.com/in/johnsmith
            Languages: English, Spanish
            """
            text_to_process = sample_text
            print("DEBUG: Using sample text for testing")
        
        if not text_to_process or len(text_to_process.strip()) < 50:
            return Response({
                'status': 'error',
                'message': 'Insufficient text content for AI processing. Please provide a document with more content.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract profile using AI with database models
        try:
            user_obj = User.objects.get(email=user_email) if user_email else None
        except User.DoesNotExist:
            user_obj = None
        
        # Check for multiple data sources and use appropriate extraction method
        if user_obj:
            # Gather all available data sources
            buyer_profile_text = user_obj.existing_buyer_profile if user_obj.existing_buyer_profile else None
            resume_text = user_obj.resume_upload if user_obj.resume_upload else None
            linkedin_data = user_obj.linkedin_data if user_obj.linkedin_data else None
            
            # If we just processed text from an uploaded file, prioritize it based on file type
            if text_to_process:
                if file_type == 'buyer_profile':
                    buyer_profile_text = text_to_process
                    print(f"DEBUG: Using uploaded buyer profile text ({len(text_to_process)} chars)")
                elif file_type == 'resume':
                    resume_text = text_to_process  
                    print(f"DEBUG: Using uploaded resume text ({len(text_to_process)} chars)")
            
            # Count available sources
            available_sources = []
            if buyer_profile_text and len(buyer_profile_text) > 100:
                available_sources.append('buyer_profile')
            if resume_text and len(resume_text) > 100:
                available_sources.append('resume')
            if linkedin_data:
                available_sources.append('linkedin')
                
            print(f"DEBUG: Available data sources: {available_sources}")
            
            # Use multi-source extraction if we have multiple sources
            if len(available_sources) > 1:
                print(f"DEBUG: Using MULTI-SOURCE extraction with {len(available_sources)} sources")
                extracted_data = extract_profile_from_multiple_sources(
                    buyer_profile_text=buyer_profile_text,
                    resume_text=resume_text,
                    linkedin_data=linkedin_data,
                    agent_name='Profile Extraction Agent',
                    user=user_obj,
                    session_id=f"multi_source_extraction_{user_email}"
                )
            else:
                # Single source extraction (fallback to original method)
                print(f"DEBUG: Using SINGLE-SOURCE extraction")
                extracted_data = extract_profile_from_text(
                    text_to_process, 
                    agent_name='Profile Extraction Agent',
                    user=user_obj,
                    session_id=f"profile_extraction_{user_email}"
                )
        else:
            # No user context, use single source extraction
            extracted_data = extract_profile_from_text(
                text_to_process, 
                agent_name='Profile Extraction Agent',
                user=user_obj,
                session_id=f"profile_extraction_anonymous"
            )
        
        print(f"DEBUG: AI extraction completed successfully")
        
        # Debug: Print extracted data structure
        print("🔍 BACKEND DEBUG - Extracted Data:")
        print(f"Type: {type(extracted_data)}")
        print(f"Keys: {list(extracted_data.keys()) if isinstance(extracted_data, dict) else 'Not a dict'}")
        
        # Sample a few fields to show structure
        sample_fields = ['first_name', 'last_name', 'background', 'company']
        for field in sample_fields:
            if field in extracted_data:
                field_data = extracted_data[field]
                print(f"  {field}: {type(field_data)} = {field_data}")
        
        # Store file content if user email is provided (for profile updates)
        if user_email and file_type:
            try:
                user = User.objects.get(email=user_email)
                if file_type == 'resume':
                    user.resume_upload = text_to_process
                    print(f"DEBUG: Stored resume content for user {user_email}")
                elif file_type == 'buyer_profile':
                    user.existing_buyer_profile = text_to_process
                    print(f"DEBUG: Stored buyer profile content for user {user_email}")
                user.save()
            except User.DoesNotExist:
                print(f"DEBUG: User with email {user_email} not found, skipping content storage")
        
        response_data = {
            'status': 'success',
            'message': 'AI profile extraction completed successfully',
            'extracted_data': extracted_data,
            'file_type': file_type,
            'text_processed': len(text_to_process) > 1000,
            'content_stored': bool(user_email and file_type)
        }
        
        print("🚀 BACKEND DEBUG - Response being sent to frontend:")
        print(f"Status: {response_data['status']}")
        print(f"Message: {response_data['message']}")
        print(f"Extracted data type: {type(response_data['extracted_data'])}")
        print(f"Sample extracted field: {response_data['extracted_data'].get('background') if isinstance(response_data['extracted_data'], dict) else 'N/A'}")
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except ImportError as e:
        print(f"DEBUG: Import error: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Failed to import AI extraction modules: {str(e)}',
            'debug_info': 'Make sure the chatGpt.py file is in the ai_profile_creation directory'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        print(f"DEBUG: Error in AI profile extraction: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'AI profile extraction failed: {str(e)}',
            'error_type': type(e).__name__
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def linkedin_import(request):
    """
    Import LinkedIn profile data for AI processing
    Accepts JSON LinkedIn profile data and stores it for multi-source extraction
    """
    try:
        user_email = request.data.get('email')
        linkedin_data = request.data.get('linkedin_data')
        
        if not user_email:
            return Response({
                'status': 'error',
                'message': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if not linkedin_data:
            return Response({
                'status': 'error',
                'message': 'LinkedIn data is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get or create user
        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'User not found. Please create a profile first.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Store LinkedIn data
        user.linkedin_data = linkedin_data
        user.save()
        
        print(f"DEBUG: LinkedIn data stored for user: {user_email}")
        print(f"DEBUG: LinkedIn data keys: {linkedin_data.keys() if isinstance(linkedin_data, dict) else 'Not a dict'}")
        
        return Response({
            'status': 'success',
            'message': 'LinkedIn data imported successfully',
            'user_email': user_email,
            'data_fields': list(linkedin_data.keys()) if isinstance(linkedin_data, dict) else []
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"DEBUG: Error in linkedin_import: {str(e)}")
        import traceback
        print(f"DEBUG: Full traceback: {traceback.format_exc()}")
        return Response({
            'status': 'error',
            'message': f'Error importing LinkedIn data: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PATCH'])
@permission_classes([AllowAny])
def update_location(request):
    print("DEBUG: update_location called with data:", request.data)
    """
    Update location section
    """
    email = request.data.get('email')
    if not email:
        return Response({
            'status': 'error',
            'message': 'Email is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Update location fields
    if 'country' in request.data:
        user.country = request.data['country']
    if 'state' in request.data:
        user.state = request.data['state']
    if 'city' in request.data:
        user.city = request.data['city']
    
    user.save()
    
    return Response({
        'status': 'success',
        'message': 'Location updated successfully'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def multi_source_extraction(request):
    """
    Multi-source AI-powered profile extraction endpoint
    Accepts resume, buyer profile files, and LinkedIn URL for comprehensive AI processing
    """
    try:
        from chatGpt import extract_profile_from_multiple_sources, extract_text_from_docx
        import tempfile
        import os
        import json

        print("DEBUG: Starting multi-source AI profile extraction...")
        print(f"DEBUG: Request FILES: {list(request.FILES.keys())}")
        print(f"DEBUG: Request data: {list(request.data.keys())}")

        # -----------------------------
        # Helpers
        # -----------------------------
        def save_upload_to_temp(uploaded_file, suffix: str) -> str:
            """
            Save an uploaded file to a temp path and return the path.
            Uses mkstemp so the file is closed before we read it (avoids Windows locking issues too).
            """
            fd, path = tempfile.mkstemp(suffix=suffix)
            try:
                with os.fdopen(fd, "wb") as f:
                    for chunk in uploaded_file.chunks():
                        f.write(chunk)
                return path
            except Exception:
                try:
                    os.unlink(path)
                except Exception:
                    pass
                raise

        def extract_text_from_pdf(pdf_path: str) -> str:
            import PyPDF2
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                pages_text = []
                for pg in reader.pages:
                    try:
                        pages_text.append(pg.extract_text() or "")
                    except Exception:
                        pages_text.append("")
            return "\n".join(pages_text).strip()

        def extract_text_from_uploaded_file(uploaded_file, label: str) -> str:
            """
            Accepts .pdf or .docx only.
            Rejects .doc (legacy) because python-docx cannot parse it reliably.
            """
            ext = os.path.splitext(uploaded_file.name)[1].lower()

            if ext not in [".pdf", ".docx", ".doc"]:
                raise ValueError(f"{label}: Unsupported file format. Please upload PDF or DOCX.")

            # Reject legacy .doc unless you add conversion support
            if ext == ".doc":
                raise ValueError(f"{label}: Legacy .doc is not supported. Please upload .docx or .pdf instead.")

            temp_path = save_upload_to_temp(uploaded_file, ext)
            try:
                print(f"DEBUG: {label} temp path: {temp_path}")
                print(f"DEBUG: {label} path exists? {os.path.exists(temp_path)} size={os.path.getsize(temp_path)} bytes")

                if ext == ".pdf":
                    text = extract_text_from_pdf(temp_path)
                    if not text:
                        raise ValueError(f"{label}: Failed to extract text from PDF. Try a different PDF or upload DOCX.")
                    return text

                # .docx
                text = extract_text_from_docx(temp_path)
                if not text:
                    raise ValueError(f"{label}: Extracted empty text from DOCX. Try a different DOCX.")
                return text

            finally:
                # Delete exactly once
                try:
                    os.unlink(temp_path)
                except FileNotFoundError:
                    pass
                except Exception as e:
                    print(f"DEBUG: Failed to delete temp file {temp_path}: {e}")

        # -----------------------------
        # Initialize data sources
        # -----------------------------
        buyer_profile_text = None
        resume_text = None
        linkedin_data = None
        questionnaire_answers = None

        # -----------------------------
        # Process buyer profile file
        # -----------------------------
        if "buyer_profile" in request.FILES:
            buyer_profile_file = request.FILES["buyer_profile"]
            print(f"DEBUG: Processing buyer_profile file: {buyer_profile_file.name}")
            try:
                buyer_profile_text = extract_text_from_uploaded_file(buyer_profile_file, "Buyer profile")
                print(f"DEBUG: Extracted buyer profile text length: {len(buyer_profile_text)} characters")
            except ValueError as ve:
                return Response({"status": "error", "message": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print(f"❌ Error processing buyer_profile: {e}")
                return Response(
                    {"status": "error", "message": "Failed to process buyer profile."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        # -----------------------------
        # Process resume file
        # -----------------------------
        if "resume" in request.FILES:
            resume_file = request.FILES["resume"]
            print(f"DEBUG: Processing resume file: {resume_file.name}")
            try:
                resume_text = extract_text_from_uploaded_file(resume_file, "Resume")
                print(f"DEBUG: Extracted resume text length: {len(resume_text)} characters")
            except ValueError as ve:
                return Response({"status": "error", "message": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print(f"❌ Error processing resume: {e}")
                return Response(
                    {"status": "error", "message": "Failed to process resume."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        # -----------------------------
        # Process LinkedIn URL
        # -----------------------------
        if "linkedin_url" in request.data:
            linkedin_url = (request.data.get("linkedin_url") or "").strip()
            if linkedin_url:
                print(f"DEBUG: Processing LinkedIn URL: {linkedin_url}")
                try:
                    from dotenv import load_dotenv
                    load_dotenv()

                    api_key = os.getenv("ENRICHLAYER_API_KEY")
                    api_url = os.getenv("ENRICHLAYER_PROFILE_URL")
                    print(f"🔑 ENV CHECK - API Key: {'Found' if api_key else 'Missing'}")
                    print(f"🔗 ENV CHECK - API URL: {'Found' if api_url else 'Missing'}")

                    if not api_key or not api_url:
                        raise Exception(
                            f"Missing environment variables - API_KEY: {bool(api_key)}, API_URL: {bool(api_url)}"
                        )

                    from linkedIn_extraction import run_linkedin_extraction
                    print("🚀 ATTEMPTING LinkedIn extraction...")
                    linkedin_data = run_linkedin_extraction(linkedin_url)

                    print("🔍 LINKEDIN SCRAPER RESPONSE:")
                    print("=" * 50)
                    print(json.dumps(linkedin_data, indent=2, ensure_ascii=False))
                    print("=" * 50)

                    populated_fields = [
                        k for k, v in (linkedin_data or {}).items()
                        if v is not None and v != "" and v != []
                    ]
                    print(f"✅ LinkedIn extraction successful - {len(populated_fields)} populated fields: {populated_fields}")

                except Exception as e:
                    print(f"❌ LinkedIn extraction failed: {str(e)}")
                    import traceback
                    print("📋 Full traceback:")
                    print(traceback.format_exc())
                    print("🔄 Falling back to basic URL data")
                    linkedin_data = {"linkedin_url": linkedin_url, "source": "manual_url_fallback"}

        # -----------------------------
        # Questionnaire answers
        # -----------------------------
        if "questionnaire_answers" in request.data:
            try:
                questionnaire_answers = json.loads(request.data["questionnaire_answers"])
                print(f"DEBUG: Questionnaire answers received: {list(questionnaire_answers.keys())}")
            except json.JSONDecodeError:
                print("DEBUG: Failed to parse questionnaire answers")

        # -----------------------------
        # Validate at least one source
        # -----------------------------
        available_sources = []
        if buyer_profile_text and len(buyer_profile_text) > 100:
            available_sources.append("buyer_profile")
        if resume_text and len(resume_text) > 100:
            available_sources.append("resume")
        if linkedin_data:
            available_sources.append("linkedin")
        if questionnaire_answers:
            available_sources.append("questionnaire")

        if not available_sources:
            return Response(
                {
                    "status": "error",
                    "message": "No valid data sources provided. Please upload at least one DOCX/PDF, provide LinkedIn, or include questionnaire answers.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        print(f"DEBUG: Processing {len(available_sources)} data sources: {available_sources}")

        # -----------------------------
        # Log what's being sent to AI
        # -----------------------------
        print("🚀 SENDING TO AI EXTRACTION:")
        print("=" * 50)
        print(f"Buyer profile text length: {len(buyer_profile_text) if buyer_profile_text else 0}")
        print(f"Resume text length: {len(resume_text) if resume_text else 0}")
        print(f"LinkedIn data keys: {list(linkedin_data.keys()) if linkedin_data else 'None'}")
        if questionnaire_answers:
            print(f"Questionnaire answers keys: {list(questionnaire_answers.keys())}")
        print("=" * 50)

        # -----------------------------
        # AI extraction
        # -----------------------------
        extracted_data = extract_profile_from_multiple_sources(
            buyer_profile_text=buyer_profile_text,
            resume_text=resume_text,
            linkedin_data=linkedin_data,
            questionnaire_answers=questionnaire_answers,
            agent_name="Profile Extraction Agent",
            user=None,
            session_id=f"multi_source_upload_{hash(str(available_sources))}",
        )

        print("🤖 AI EXTRACTION RESPONSE:")
        print("=" * 50)
        if isinstance(extracted_data, dict):
            print(json.dumps(extracted_data, indent=2, ensure_ascii=False))
        else:
            print(f"Unexpected AI response type: {type(extracted_data)}")
            print(f"AI response: {extracted_data}")
        print("=" * 50)

        # -----------------------------
        # Normalize {"value": ..., "confidence": ...} shapes
        # -----------------------------
        if isinstance(extracted_data, dict):
            for field_name, field_data in list(extracted_data.items()):
                if isinstance(field_data, dict) and "value" in field_data:
                    extracted_data[field_name] = field_data["value"]

            # Handle stringified JSON for specific array fields if needed
            for key in ["education", "professional_experience"]:
                if key in extracted_data and isinstance(extracted_data[key], str):
                    try:
                        extracted_data[key] = json.loads(extracted_data[key])
                    except Exception:
                        pass

        response_data = {
            "status": "success",
            "message": f"Multi-source AI extraction completed using {len(available_sources)} sources",
            "extracted_data": extracted_data,
            "sources_processed": available_sources,
            "sources_count": len(available_sources),
            "debug_info": {
                "questionnaire_questions_answered": len(questionnaire_answers) if questionnaire_answers else 0,
                "linkedin_data_available": linkedin_data is not None,
                "resume_text_length": len(resume_text) if resume_text else 0,
                "buyer_profile_text_length": len(buyer_profile_text) if buyer_profile_text else 0,
            },
        }

        print("🚀 BACKEND DEBUG - Multi-source response being sent to frontend:")
        print(f"Status: {response_data['status']}")
        print(f"Sources: {response_data['sources_processed']}")
        print(f"Sources count: {response_data['sources_count']}")

        return Response(response_data, status=status.HTTP_200_OK)

    except ImportError as e:
        print(f"DEBUG: Import error: {str(e)}")
        return Response(
            {
                "status": "error",
                "message": f"Failed to import AI extraction modules: {str(e)}",
                "debug_info": "Make sure the chatGpt.py file is in the ai_profile_creation directory",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    except Exception as e:
        print(f"DEBUG: Error in multi-source AI profile extraction: {str(e)}")
        import traceback
        print(f"DEBUG: Full traceback: {traceback.format_exc()}")
        return Response(
            {"status": "error", "message": f"Multi-source AI profile extraction failed: {str(e)}", "error_type": type(e).__name__},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

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
        
        return Response({
            'status': 'success',
            'message': 'Access granted',
            'email': email,
            'access_granted': True
        })
        
    except Exception as e:
        print(f"💥 BACKEND ERROR: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

