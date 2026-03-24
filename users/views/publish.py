from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


def _resolve_user_from_request(request):
    """
    Resolve user from:
    1) Authorization: Bearer <api_token>
    2) session-authenticated request.user
    """
    # Bearer api_token
    auth = request.META.get("HTTP_AUTHORIZATION") or request.META.get("Authorization")
    if auth and isinstance(auth, str) and auth.lower().startswith("bearer "):
        token = auth.split(None, 1)[1].strip()
        user = User.objects.filter(api_token=token).first()
        if user:
            return user

    # Session auth
    u = getattr(request, "user", None)
    if u and getattr(u, "is_authenticated", False):
        return u

    return None


@api_view(["POST"])
@permission_classes([AllowAny])
def publish_profile(request):
    print("Publish profile request received")
    """
    Publish the current user's profile.
    Used by the dashboard.

    Auth:
      - Authorization: Bearer <api_token> OR session user
    """
    user = _resolve_user_from_request(request)
    if not user:
        return Response(
            {"success": False, "message": "Authentication required"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    user.published = True
    user.public_token = User.ensure_public_token(user, save=False)

    # (optional) keep profile_completed consistent
    if not getattr(user, "profile_completed", False):
        user.profile_completed = True
        user.save(update_fields=["published", "public_token", "profile_completed"])
    else:
        user.save(update_fields=["published", "public_token"])

    return Response(
        {
            "success": True,
            "message": "Profile published",
            "published": True,
            "public_token": str(user.public_token),
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def unpublish_profile(request):
    user = _resolve_user_from_request(request)
    if not user:
        return Response(
            {"success": False, "message": "Authentication required"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    user.published = False



    user.save(update_fields=["published", "public_token"])

    return Response(
        {"success": True, "message": "Profile unpublished", "published": False},
        status=status.HTTP_200_OK,
    )

@api_view(["POST"])
@permission_classes([AllowAny])
def publish_profile_dev(request):
    """
    Development-only publish endpoint: publish profile by email without authentication.
    Only available when settings.DEBUG is True.

    Expected body: { "email": "user@example.com" }
    """
    if not getattr(settings, "DEBUG", False):
        return Response(
            {"success": False, "message": "Not allowed"},
            status=status.HTTP_403_FORBIDDEN,
        )

    email = request.data.get("email")
    if not email:
        return Response(
            {"success": False, "message": "Email is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = User.objects.filter(email=email).first()
    if not user:
        return Response(
            {"success": False, "message": "User not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    user.published = True
    if not getattr(user, "public_token", None):
        user.public_token = User.ensure_public_token(user, save=False)

    if not getattr(user, "profile_completed", False):
        user.profile_completed = True
        user.save(update_fields=["published", "public_token", "profile_completed"])
    else:
        user.save(update_fields=["published", "public_token"])

    return Response(
        {
            "success": True,
            "message": "Profile published (dev)",
            "published": True,
            "public_token": str(user.public_token),
        },
        status=status.HTTP_200_OK,
    )
