from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.views.decorators.csrf import ensure_csrf_cookie
from django.conf import settings
from django.contrib.auth import get_user_model
import uuid
import re
import json
import logging

logger = logging.getLogger(__name__)

from ..serializers import (
    UserRegistrationSerializer, UserSerializer, UserUpdateSerializer
)

User = get_user_model()


# Public profile view by token (for preview/public-profile page)
@api_view(["GET"])
@permission_classes([AllowAny])
def public_profile_view(request, token=None):
    """
    - /api/public-profile/<token>/ : public preview (only if published)
    - /api/public-profile/        : current user (Bearer api_token or session)
    """
    try:
        user = None

        if token:
            user = User.objects.get(public_token=token)

            # Only token-based access is restricted to published profiles
            if not getattr(user, "published", False):
                return Response({"success": False, "message": "User not found"}, status=404)

        else:
            # Current user: Bearer token first, then session auth
            auth_header = request.META.get("HTTP_AUTHORIZATION") or request.META.get("Authorization")
            if auth_header and isinstance(auth_header, str) and auth_header.lower().startswith("bearer "):
                token_val = auth_header.split(None, 1)[1].strip()
                user = User.objects.filter(api_token=token_val).first()

            if not user and request.user and getattr(request.user, "is_authenticated", False):
                user = request.user

            if not user:
                return Response({"success": False, "message": "Authentication required"}, status=401)

        # ---- keep your existing serializer/public_data shaping from here down ----
        serializer = UserSerializer(user)
        public_data = dict(serializer.data) if serializer.data is not None else {}
        public_data.pop("public_token", None)
        public_data.pop("api_token", None)

        # ... keep the rest of your existing normalization (areas_of_expertise, skillsList, etc.) ...

        return Response({"success": True, "data": public_data})

    except User.DoesNotExist:
        return Response({"success": False, "message": "User not found"}, status=404)

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
        'targetStatement': 'target_statement',
        'investmentExperience': 'investment_experience',
        'dealSizePreference': 'deal_size_preference',
        'industryFocus': 'industry_focus',
        'geographicFocus': 'geographic_focus',
    }
    
    mapped_data = {}
    for key, value in data.items():
        backend_field = field_mapping.get(key, key)
        mapped_data[backend_field] = value
    
    if updating_existing_user:
        mapped_data.pop('username', None)
        print(f"DEBUG: Removed username from data for existing user update")
    else:
        if 'email' in mapped_data and 'username' not in mapped_data:
            mapped_data['username'] = mapped_data['email']
    
    mapped_data = normalize_array_fields(mapped_data)
    
    return mapped_data


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
        if self.request.user.is_superuser:
            return User.objects.all()
        else:
            return User.objects.filter(id=self.request.user.id)


def log_create_profile_request(request):
    logger.warning("=== DEBUG /api/create-profile/ ===")
    logger.warning("method=%s path=%s", getattr(request, "method", None), getattr(request, "path", None))
    logger.warning("content_type=%s", getattr(request, "content_type", None))

    data = getattr(request, "data", None)
    if data is not None:
        try:
            logger.warning("request.data keys=%s", list(data.keys()))
            for k in ["email", "education", "certifications", "professional_experience", "work_experience", "experience"]:
                v = data.get(k, None)
                logger.warning("request.data[%s]=%s", k, v)
        except Exception as e:
            logger.exception("Failed to log request.data: %s", e)

    post = getattr(request, "POST", None)
    if post is not None:
        try:
            logger.warning("request.POST keys=%s", list(post.keys()))
        except Exception as e:
            logger.exception("Failed to log request.POST: %s", e)

    raw = None
    if data is not None:
        raw = data.get("professional_experience") or data.get("work_experience") or data.get("experience")

    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
            logger.warning("parsed experience type=%s len=%s", type(parsed).__name__, len(parsed) if hasattr(parsed, "__len__") else None)
            logger.warning("parsed experience=%s", parsed)
        except Exception as e:
            logger.exception("JSON parse error for experience field: %s", e)

    logger.warning("=== DEBUG /api/create-profile/ END ===")


@api_view(['POST'])
@permission_classes([AllowAny])
def create_profile(request):
    """
    Create or update user profile
    """
    log_create_profile_request(request)
    print(f"🚀 CREATE_PROFILE called!")
    print(f"🔍 Raw request.data: {request.data}")
    print(f"🔍 Request method: {request.method}")
    print(f"🔍 Content-Type: {request.content_type}")
    
    if 'professional_experience' in request.data:
        prof_exp = request.data['professional_experience']
        print(f"💼 Professional experience received:")
        print(f"   Type: {type(prof_exp)}")
        print(f"   Length: {len(prof_exp) if isinstance(prof_exp, (list, dict)) else 'N/A'}")
        print(f"   Content: {prof_exp}")
    else:
        print(f"❌ No 'professional_experience' field in request.data")
    
    email = request.data.get('email')
    user_exists = User.objects.filter(email=email).exists() if email else False
    
    print(f"📧 Email: {email}")
    print(f"👤 User exists: {user_exists}")
    
    mapped_data = map_frontend_fields(request.data, updating_existing_user=user_exists)
    print(f"🗺️  Mapped data: {mapped_data}")
    
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
    
    try:
        user = User.objects.get(email=email)
        print(f"🔄 Updating existing user: {user.email} (ID: {user.id})")
        serializer = UserRegistrationSerializer(
            user, 
            data=mapped_data, 
            partial=True,
            context={'email_verified': email_verified, 'updating_existing': True}
        )
    except User.DoesNotExist:
        print(f"🆕 Creating new user for: {email}")
        if email_verified:
            serializer = UserRegistrationSerializer(
                data=mapped_data,
                context={'email_verified': True}
            )
        else:
            serializer = UserRegistrationSerializer(data=mapped_data)
    
    if serializer.is_valid():
        print(f"✅ Serializer is valid!")
        try:
            # Debug: show acquisition_target present in mapped_data before save
            print(f"🔍 MAPPED acquisition_target before save: {mapped_data.get('acquisition_target')}")
            user = serializer.save()
            # Debug: show acquisition_target on saved user
            print(f"💾 User saved successfully: {user.email} (ID: {user.id})")
            print(f"🔎 Saved user.acquisition_target: {getattr(user, 'acquisition_target', None)}")
            
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
    print("🔥 get_user_profile from users/views/profile.py")

    email = request.GET.get('email')
    
    if not email:
        return Response({
            'success': False,
            'message': 'Email parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
        print(f"📡 get_user_profile: email={user.email} id={user.id}")

        # Debug: log acquisition_target being returned
        print(f"📡 get_user_profile: user.email={user.email} acquisition_target={user.acquisition_target}")

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
                "targetStatement": user.target_statement,
                "target_statement": user.target_statement,
                'acquisitionTargetRaw': user.existing_buyer_profile,
                'website': user.website,
                'bio': user.bio,
                'skills': user.skills,
                'languages': user.languages,
                'profileCompleted': user.profile_completed,
                'published': user.published,
                'createdAt': user.created_at.isoformat(),
                'updatedAt': user.updated_at.isoformat(),
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_dashboard(request):
    user = request.user
    user_data = UserSerializer(user).data
    
    return Response({
        'message': f'Welcome to your dashboard, {user.first_name}!',
        'user': user_data,
        'dashboard_data': {
            'profile_completion': 100,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'member_since': user.created_at.isoformat(),
            'total_profiles': 1
        }
    }, status=status.HTTP_200_OK)
