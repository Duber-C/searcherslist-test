from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
)
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from rest_framework.authentication import SessionAuthentication
from ..authentication import ApiTokenAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from django.conf import settings
from ..serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    UserUpdateSerializer,
    SendOTPSerializer,
    VerifyOTPSerializer,
    OTPSerializer,
)
from ..otp_models import OTP
from ..email_service import EmailService
import sys
import os
import uuid
import secrets
from django.core.exceptions import ValidationError

# Add the ai_profile_creation directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "ai_profile_creation"))

User = get_user_model()



class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user_data = UserSerializer(user).data
            return Response(
                {
                    "message": "Profile created successfully!",
                    "user": user_data,
                    "profile_id": user.id,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {
                "message": "Error creating profile. Please check your information.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method == "GET":
            return UserSerializer
        return UserUpdateSerializer


class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return User.objects.all()
        else:
            return User.objects.filter(id=self.request.user.id)


def normalize_array_fields(data):
    if "education" in data and isinstance(data["education"], list):
        normalized_education = []
        for edu in data["education"]:
            if edu and isinstance(edu, dict):
                normalized_edu = {
                    "school": str(edu.get("school", "Unknown")).strip() or "Unknown",
                    "degree": str(edu.get("degree", "Unknown")).strip() or "Unknown",
                    "field": str(edu.get("field", "General")).strip() or "General",
                    "years": str(edu.get("years", "Unknown")).strip() or "Unknown",
                    "description": str(edu.get("description", "None")).strip()
                    or "None",
                }
                for key, value in normalized_edu.items():
                    if value.lower() in ["null", "none", ""]:
                        if key == "degree":
                            normalized_edu[key] = "Unknown"
                        elif key == "field":
                            normalized_edu[key] = "General"
                        elif key == "description":
                            normalized_edu[key] = "None"
                        else:
                            normalized_edu[key] = "Unknown"
                normalized_education.append(normalized_edu)
        data["education"] = normalized_education

    if "professional_experience" in data and isinstance(
        data["professional_experience"], list
    ):
        normalized_experience = []
        for exp in data["professional_experience"]:
            if exp and isinstance(exp, dict):
                normalized_exp = {
                    "company": str(exp.get("company", "Unknown")).strip() or "Unknown",
                    "title": str(exp.get("title", "Unknown")).strip() or "Unknown",
                    "duration": str(exp.get("duration", "Unknown")).strip()
                    or "Unknown",
                    "description": str(exp.get("description", "None")).strip()
                    or "None",
                    "achievements": str(exp.get("achievements", "None")).strip()
                    or "None",
                }
                for key, value in normalized_exp.items():
                    if value.lower() in ["null", "none", ""]:
                        if key in ["description", "achievements"]:
                            normalized_exp[key] = "None"
                        else:
                            normalized_exp[key] = "Unknown"
                normalized_experience.append(normalized_exp)
        data["professional_experience"] = normalized_experience

    return data


def map_frontend_fields(data, updating_existing_user=False):
    field_mapping = {
        "firstName": "first_name",
        "lastName": "last_name",
        "phoneNumber": "phone_number",
        "linkedinUrl": "linkedin_url",
        "currentRole": "current_role",
        "yearsExperience": "years_experience",
        "valueProposition": "value_proposition",
        "areasOfExpertise": "areas_of_expertise",
        "investmentExperience": "investment_experience",
        "dealSizePreference": "deal_size_preference",
        "industryFocus": "industry_focus",
        "geographicFocus": "geographic_focus",
    }
    mapped_data = {}
    for key, value in data.items():
        backend_field = field_mapping.get(key, key)
        mapped_data[backend_field] = value
    if updating_existing_user:
        mapped_data.pop("username", None)
    else:
        if "email" in mapped_data and "username" not in mapped_data:
            mapped_data["username"] = mapped_data["email"]
    mapped_data = normalize_array_fields(mapped_data)
    return mapped_data

import json
import logging

logger = logging.getLogger(__name__)

def log_create_profile_request(request):
    logger.warning("=== DEBUG /api/create-profile/ ===")
    logger.warning("method=%s path=%s", getattr(request, "method", None), getattr(request, "path", None))
    logger.warning("content_type=%s", getattr(request, "content_type", None))

    # DRF: request.data (works for multipart/form-data)
    data = getattr(request, "data", None)
    if data is not None:
      try:
        logger.warning("request.data keys=%s", list(data.keys()))
        for k in ["email", "education", "certifications", "professional_experience", "work_experience", "experience"]:
            v = data.get(k, None)
            logger.warning("request.data[%s]=%s", k, v)
      except Exception as e:
        logger.exception("Failed to log request.data: %s", e)

    # Django: request.POST
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

@api_view(["POST"])
@permission_classes([AllowAny])
def create_profile(request):
    log_create_profile_request(request)

    print(f"🚀 CREATE_PROFILE called!")
    print(f"🔍 Raw request.data: {request.data}")
    print(f"🔍 Request method: {request.method}")
    print(f"🔍 Content-Type: {request.content_type}")
    if "professional_experience" in request.data:
        prof_exp = request.data["professional_experience"]
        print(f"💼 Professional experience received:")
        print(f"   Type: {type(prof_exp)}")
        print(
            f"   Length: {len(prof_exp) if isinstance(prof_exp, (list, dict)) else 'N/A'}"
        )
        print(f"   Content: {prof_exp}")
    else:
        print(f"❌ No 'professional_experience' field in request.data")
    email = request.data.get("email")
    user_exists = User.objects.filter(email=email).exists() if email else False
    mapped_data = map_frontend_fields(request.data, updating_existing_user=user_exists)
    email_verified = mapped_data.get("email_verified") == "true"
    try:
        user = User.objects.get(email=email)
        serializer = UserRegistrationSerializer(
            user,
            data=mapped_data,
            partial=True,
            context={"email_verified": email_verified, "updating_existing": True},
        )
    except User.DoesNotExist:
        if email_verified:
            serializer = UserRegistrationSerializer(
                data=mapped_data, context={"email_verified": True}
            )
        else:
            serializer = UserRegistrationSerializer(data=mapped_data)
    if serializer.is_valid():
        try:
            user = serializer.save()
            profile_complete = False
            try:
                requested_complete = mapped_data.get("profile_completed")
                if requested_complete is not None:
                    if isinstance(requested_complete, str):
                        requested_complete = requested_complete.lower() in [
                            "true",
                            "1",
                            "yes",
                            "on",
                        ]
                    requested_complete = bool(requested_complete)
                if requested_complete:
                    user.profile_completed = True
                    user.save(update_fields=["profile_completed"])
                    profile_complete = True
                else:
                    profile_complete = user.mark_profile_complete()
            except Exception:
                profile_complete = user.mark_profile_complete()
            return Response(
                {
                    "message": "Profile saved successfully!",
                    "profile_id": f"profile_{user.id}",
                    "profile_completed": profile_complete,
                    "user": {
                        "id": user.id,
                        "name": f"{user.first_name} {user.last_name}",
                        "email": user.email,
                        "phone": user.phone_number,
                        "location": f"{user.city}, {user.state}, {user.country}",
                        "linkedin": user.linkedin_url,
                        "profile_completed": user.profile_completed,
                        "created_at": user.created_at.isoformat(),
                    },
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            import traceback

            return Response(
                {
                    "message": "Error creating profile. Please try again.",
                    "error": str(e),
                    "debug_info": {
                        "email_verified": email_verified,
                        "email": email,
                        "user_exists": User.objects.filter(email=email).exists(),
                    },
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    return Response(
        {
            "message": "Invalid data provided. Please check your information.",
            "errors": serializer.errors,
            "debug_info": {"email_verified": email_verified, "email": email},
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["GET"])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def get_user_profile(request):
    email = request.GET.get("email")
    if not email:
        return Response(
            {"success": False, "message": "Email parameter is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        user = User.objects.get(email=email)
        return Response(
            {
                "success": True,
                "user_exists": True,
                "profile_completed": user.profile_completed,
                "data": {
                    "id": user.id,
                    "email": user.email,
                    "firstName": user.first_name,
                    "lastName": user.last_name,
                    "phoneNumber": user.phone_number,
                    "country": user.country,
                    "city": user.city,
                    "state": user.state,
                    "linkedinUrl": user.linkedin_url,
                    "background": user.background,
                    "valueProposition": user.value_proposition,
                    "targetStatement": user.target_statement,
                    "areasOfExpertise": user.areas_of_expertise,
                    "investmentExperience": user.investment_experience,
                    "dealSizePreference": user.deal_size_preference,
                    "industryFocus": user.industry_focus,
                    "geographicFocus": user.geographic_focus,
                    "currentRole": user.current_role,
                    "company": user.company,
                    "yearsExperience": user.years_experience,
                    "education": user.education,
                    "professionalExperience": user.professional_experience,
                    "certifications": user.certifications,
                    "achievements": user.achievements,
                    "website": user.website,
                    "bio": user.bio,
                    "skills": user.skills,
                    "languages": user.languages,
                    "profileCompleted": user.profile_completed,
                    "published": user.published,
                    "createdAt": user.created_at.isoformat(),
                    "updatedAt": user.updated_at.isoformat(),
                    "resumeUrl": user.resume.url if user.resume else None,
                    "buyerProfileUrl": (
                        user.buyer_profile.url if user.buyer_profile else None
                    ),
                    "publicToken": (
                        str(user.public_token) if user.public_token else None
                    ),
                },
            },
            status=status.HTTP_200_OK,
        )
    except User.DoesNotExist:
        return Response(
            {
                "success": True,
                "user_exists": False,
                "profile_completed": False,
                "data": {},
            },
            status=status.HTTP_200_OK,
        )




@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    return Response(
        {"status": "healthy", "message": "Searcher API is running", "version": "1.0.0"},
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def debug_resolve_token(request):
    try:
        if not getattr(settings, "DEBUG", False):
            return Response(
                {"success": False, "message": "Not allowed"},
                status=status.HTTP_403_FORBIDDEN,
            )
        auth = request.META.get("HTTP_AUTHORIZATION") or request.META.get(
            "Authorization"
        )
        if (
            not auth
            or not isinstance(auth, str)
            or not auth.lower().startswith("bearer ")
        ):
            return Response(
                {"success": False, "message": "Authorization Bearer token required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        token = auth.split(None, 1)[1].strip()
        masked = f"****{token[-6:]}" if len(token) > 6 else token
        print(f"🔍 debug_resolve_token received masked token: {masked}")
        resolved_user = None
        try:
            resolved_user = User.objects.filter(api_token=token).first()
            if resolved_user:
                print(
                    f"✅ Token resolved to user: {resolved_user.email} (ID: {resolved_user.id})"
                )
        except Exception as e:
            print(f"❌ Error resolving token to user: {e}")
        user_info = None
        try:
            u = request.user
            if u and getattr(u, "is_authenticated", False):
                user_info = {
                    "email": getattr(u, "email", None),
                    "id": getattr(u, "id", None),
                    "published": getattr(u, "published", None),
                    "profile_completed": getattr(u, "profile_completed", None),
                    "public_token": (
                        str(getattr(u, "public_token", None))
                        if getattr(u, "public_token", None)
                        else None
                    ),
                }
            else:
                user_info = None
        except Exception as e:
            print(f"❌ Error building user_info from request.user: {e}")
            user_info = None
        return Response(
            {
                "token": token,
                "resolved_user": resolved_user and resolved_user.email,
                "user": user_info,
            },
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        print(f"💥 debug_resolve_token error: {e}")
        return Response(
            {"success": False, "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def save_professional_experience_data(request):
    """
    Endpoint to save professional experience data directly to the database
    """
    try:
        email = request.data.get("email")
        experience_data = request.data.get("experience_data")

        if not email:
            return Response(
                {"status": "error", "message": "Email is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not experience_data:
            return Response(
                {"status": "error", "message": "Experience data is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

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
                    "username": email,
                    "is_active": True,
                    "profile_completed": False,
                },
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
            lines = experience_data.strip().split("\n")

            current_experience = None
            for line in lines:
                line = line.strip()
                if not line:
                    if current_experience:
                        experiences.append(current_experience)
                        current_experience = None
                    continue

                # Check if this is a new experience (starts with number)
                if line.split(".")[0].strip().isdigit():
                    if current_experience:
                        experiences.append(current_experience)

                    # Parse new experience
                    line_without_number = ".".join(line.split(".")[1:]).strip()

                    # Extract title, company, and duration
                    experience = {
                        "id": len(experiences) + 1,
                        "title": "",
                        "company": "",
                        "duration": "",
                        "description": line_without_number,
                    }

                    # Try to parse structure
                    if " at " in line_without_number:
                        parts = line_without_number.split(" at ", 1)
                        experience["title"] = parts[0].strip()
                        remaining = parts[1].strip()

                        # Look for duration pattern
                        import re

                        date_pattern = r"\(([^)]+)\)"
                        date_match = re.search(date_pattern, remaining)

                        if date_match:
                            experience["duration"] = date_match.group(1)
                            experience["company"] = remaining[
                                : date_match.start()
                            ].strip()
                            # Description is everything after the date
                            desc_start = date_match.end()
                            if desc_start < len(remaining):
                                desc_text = remaining[desc_start:].strip()
                                if desc_text:
                                    experience["description"] = desc_text
                        else:
                            experience["company"] = remaining

                    current_experience = experience

                elif current_experience and line:
                    # Add to description of current experience
                    if current_experience["description"] and current_experience[
                        "description"
                    ] != (
                        current_experience["title"]
                        + " at "
                        + current_experience["company"]
                    ):
                        current_experience["description"] += "\n" + line
                    else:
                        current_experience["description"] = line

            # Add the last experience
            if current_experience:
                experiences.append(current_experience)

            user.professional_experience = experiences
            print(f"DEBUG: Parsed and saved {len(experiences)} experiences from text")

        user.save()

        return Response(
            {
                "status": "success",
                "message": f"Successfully saved {len(user.professional_experience)} professional experiences",
                "experiences_count": len(user.professional_experience),
                "experiences": user.professional_experience,
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        print(f"DEBUG: Error saving professional experience: {str(e)}")
        import traceback

        print(f"DEBUG: Full traceback: {traceback.format_exc()}")
        return Response(
            {
                "status": "error",
                "message": f"Failed to save professional experience: {str(e)}",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
