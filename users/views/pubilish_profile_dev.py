from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import csrf_exempt

from users.models.user import User


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def publish_profile_dev(request):
    print("Publish profile (dev) request received")
    try:
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
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"success": False, "message": "User not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        user.published = True
        if not user.profile_completed:
            user.profile_completed = True
            user.save(update_fields=["published", "profile_completed"])
        else:
            user.save(update_fields=["published"])
        if not user.public_token:
            user.public_token = User.ensure_public_token(user, save=False)
            user.save(update_fields=["public_token"])
        return Response(
            {
                "success": True,
                "message": "Profile published (dev)",
                "published": user.published,
                "public_token": str(user.public_token),
            },
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        return Response(
            {
                "success": False,
                "message": "Error publishing profile (dev)",
                "error": str(e),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
