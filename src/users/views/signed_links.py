from django.utils import timezone

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from users.models import User


@api_view(['POST'])
def create_signed_link(request):
    """
    Create a signed link for sharing a user's profile or other resources.
    Expects JSON with `user_id`, `resource` and optional `expires_in_seconds`.
    """
    try:
        user_id = request.data.get('user_id')
        resource = request.data.get('resource')
        expires_in = int(request.data.get('expires_in_seconds', 3600))

        if not user_id or not resource:
            return Response({'status': 'error', 'message': 'user_id and resource required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'status': 'error', 'message': 'user not found'}, status=status.HTTP_404_NOT_FOUND)

        # TODO: create or use de SignedLink model
        # expires_at = timezone.now() + timezone.timedelta(seconds=expires_in)
        # signed = SignedLink.objects.create(user=user, resource=resource, expires_at=expires_at)

        return Response({'status': 'success', 'signed_link': signed.token})

    except Exception as e:
        print(f"ERROR: create_signed_link failed: {e}")
        return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def validate_signed_link(request, token):
    """
    Validate a signed link token and return the referenced resource if valid.
    """
    try:
        from users.models.link import SignedLink

        try:
            signed = SignedLink.objects.get(token=token)
        except SignedLink.DoesNotExist:
            return Response({'status': 'error', 'message': 'invalid token'}, status=status.HTTP_404_NOT_FOUND)

        if signed.expires_at and signed.expires_at < timezone.now():
            return Response({'status': 'error', 'message': 'token expired'}, status=status.HTTP_410_GONE)

        return Response({'status': 'success', 'user_id': signed.user_id, 'resource': signed.resource})

    except Exception as e:
        print(f"ERROR: validate_signed_link failed: {e}")
        return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
