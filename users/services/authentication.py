from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from django.contrib.auth import get_user_model

User = get_user_model()

class ApiTokenAuthentication(BaseAuthentication):
    """Authenticate requests using `Authorization: Bearer <api_token>` header.

    Returns (user, None) when token matches a `User.api_token` value.
    If header is missing, returns None to allow other authenticators to run.
    If token is present but invalid, raises AuthenticationFailed.
    """

    def authenticate(self, request):
        auth = request.META.get('HTTP_AUTHORIZATION') or request.META.get('Authorization')
        if not auth or not isinstance(auth, str):
            return None

        auth_l = auth.lower()
        if not auth_l.startswith('bearer '):
            return None

        token = auth.split(None, 1)[1].strip()
        if not token:
            return None

        try:
            user = User.objects.get(api_token=token)
            return (user, None)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid API token')
