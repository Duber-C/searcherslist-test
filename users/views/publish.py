from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authentication import SessionAuthentication
from ..authentication import ApiTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.conf import settings
import uuid

User = get_user_model()


@csrf_exempt
@api_view(['POST'])
@authentication_classes([ApiTokenAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def publish_profile(request):
    # Avoid accessing request.user attributes directly — user may be AnonymousUser
    pu_email = getattr(getattr(request, 'user', None), 'email', 'Anonymous')
    pu_id = getattr(getattr(request, 'user', None), 'id', 'N/A')
    print(f"🚀 PUBLISH_PROFILE called. request.user: {pu_email} (ID: {pu_id})")
    try:
        # Determine acting user: prefer Bearer token owner if provided, otherwise fall back to session user
        user = None
        token_owner = None
        auth = request.META.get('HTTP_AUTHORIZATION') or request.META.get('Authorization')
        if auth and isinstance(auth, str) and auth.lower().startswith('bearer '):
            token = auth.split(None, 1)[1].strip()
            try:
                token_owner = User.objects.get(api_token=token)
            except User.DoesNotExist:
                token_owner = None

        if token_owner:
            user = token_owner
        elif getattr(request, 'user', None) and request.user.is_authenticated:
            user = request.user

        if not user:
            return Response({'success': False, 'message': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            auth_method = 'bearer' if token_owner else 'session'
            print(f"🔐 publish_profile called by user: email={getattr(user, 'email', None)} id={getattr(user, 'id', None)} auth_method={auth_method}")
        except Exception:
            print(f"🔐 publish_profile called by user (repr): {repr(user)}")
        print(f"🔍 Request.COOKIES: {request.COOKIES}")
        print(f"🔍 Request META Cookie header: {request.META.get('HTTP_COOKIE')}")

        # Set published flag
        user.published = True

        # If profile wasn't completed, mark it completed now
        if not user.profile_completed:
            user.profile_completed = True
            user.save(update_fields=['published', 'profile_completed'])
        else:
            user.save(update_fields=['published'])

        # Ensure a public token exists for shareable public profile links
        if not user.public_token:
            user.public_token = uuid.uuid4()
            user.save(update_fields=['public_token'])

        # Ensure an api_token exists for bearer auth (generate if missing)
        if not getattr(user, 'api_token', None):
            user.api_token = uuid.uuid4().hex
            user.save(update_fields=['api_token'])

        return Response({
            'success': True,
            'message': 'Profile published successfully',
            'published': user.published,
            'profile_completed': user.profile_completed,
            'public_token': str(user.public_token) if user.public_token else None,
            'api_token': user.api_token
        }, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"❌ Error publishing profile: {e}")
        return Response({'success': False, 'message': 'Error publishing profile', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@csrf_exempt
@api_view(['POST'])
@authentication_classes([ApiTokenAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def unpublish_profile(request):
    # Avoid accessing request.user attributes directly — user may be AnonymousUser
    up_email = getattr(getattr(request, 'user', None), 'email', 'Anonymous')
    up_id = getattr(getattr(request, 'user', None), 'id', 'N/A')
    print(f"🚫 UNPUBLISH_PROFILE called. request.user: {up_email} (ID: {up_id})")
    try:
        # Determine acting user: prefer Bearer token owner if provided, otherwise fall back to session user
        user = None
        token_owner = None
        auth_header = request.META.get('HTTP_AUTHORIZATION') or request.META.get('Authorization')
        if auth_header and isinstance(auth_header, str) and auth_header.lower().startswith('bearer '):
            token = auth_header.split(None, 1)[1].strip()
            try:
                token_owner = User.objects.get(api_token=token)
            except User.DoesNotExist:
                token_owner = None

        if token_owner:
            user = token_owner
        elif getattr(request, 'user', None) and request.user.is_authenticated:
            user = request.user

        if not user:
            return Response({'success': False, 'message': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            auth_method = 'bearer' if token_owner else 'session'
            print(f"🔐 unpublish_profile called by user: email={getattr(user, 'email', None)} id={getattr(user, 'id', None)} auth_method={auth_method}")
        except Exception:
            print(f"🔐 unpublish_profile called by user (repr): {repr(user)}")
        if auth_header:
            try:
                print(f"🔑 Authorization header received: {auth_header}")
                if auth_header.lower().startswith('bearer '):
                    token = auth_header.split(None, 1)[1].strip()
                    masked = f"****{token[-6:]}" if len(token) > 6 else token
                    print(f"🔒 Bearer token (masked): {masked}")
            except Exception:
                pass
        print(f"🔍 Request.COOKIES: {request.COOKIES}")
        print(f"🔍 Request META Cookie header: {request.META.get('HTTP_COOKIE')}")

        user.published = False
        user.save(update_fields=['published'])
        print(f"🔒 Profile unpublished for user: {user.email} (ID: {user.id}) status {user.published}")
        if user.public_token:
            user.public_token = None
            user.save(update_fields=['public_token'])

        return Response({'success': True, 'message': 'Profile unpublished', 'published': user.published, 'public_token': None}, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"❌ Error unpublishing profile: {e}")
        return Response({'success': False, 'message': 'Error unpublishing profile', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
