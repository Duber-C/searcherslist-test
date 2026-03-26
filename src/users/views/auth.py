import secrets

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from users.models.user import User
from users.models.otp import OTPVerification


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
        
        # Create new OTP using the OTPVerification model
        otp_verification = OTPVerification.objects.create(
            email=email,
            signed_link=None  # Can be null for existing users
        )
        
        print(f"✅ Created new OTP for {email}: {otp_verification.otp_code}")
        
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

        try:
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
    from ..serializers import VerifyOTPSerializer, UserSerializer

    serializer = VerifyOTPSerializer(data=request.data)
    
    if serializer.is_valid():
        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp_code']
        
        try:
            otp = OTPVerification.get_valid_otp(email)
            
            if not otp:
                return Response({
                    'success': False,
                    'message': 'No valid OTP found. Please request a new one.',
                    'require_new_otp': True
                }, status=status.HTTP_400_BAD_REQUEST)
            
            is_valid, message = otp.verify(otp_code)
            
            if is_valid:
                if otp.user_exists:
                    user = otp.user
                    user_data = UserSerializer(user).data

                    api_token = None
                    try:
                        api_token = secrets.token_hex(32)
                        user.api_token = api_token
                        user.save(update_fields=['api_token'])
                    except Exception as e:
                        print(f"❌ Failed to generate/save api_token for {user.email}: {e}")

                    if user.profile_completed:
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
            from ..models import User
            resolved_user = User.objects.filter(api_token=token).first()
            if resolved_user:
                print(f"✅ Token resolved to user: {resolved_user.email} (ID: {resolved_user.id})")
        except Exception as e:
            print(f"❌ Error resolving token to user: {e}")

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
