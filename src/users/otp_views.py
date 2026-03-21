from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import OTP
from .email_service import EmailService
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

@api_view(['POST'])
def generate_otp(request):
    """
    Generate and send OTP to email address
    
    Request body:
    {
        "email": "user@example.com"
    }
    
    Response:
    {
        "success": true,
        "message": "OTP sent successfully!",
        "email": "user@example.com",
        "expires_in_minutes": 10
    }
    """
    try:
        email = request.data.get('email')
        
        if not email:
            return Response({
                'success': False,
                'message': 'Email address is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create and send OTP
        otp_instance = OTP(email=email)
        otp_instance.save()
        
        # Send email using EmailService
        email_service = EmailService()
        email_sent = email_service.send_otp_email(email, otp_instance.otp_code)
        
        if email_sent:
            logger.info(f"OTP generated and sent successfully to {email}")
            return Response({
                'success': True,
                'message': 'OTP sent successfully!',
                'email': email,
                'expires_in_minutes': 10
            }, status=status.HTTP_200_OK)
        else:
            # Delete the OTP if email sending failed
            otp_instance.delete()
            return Response({
                'success': False,
                'message': 'Failed to send OTP email. Please try again.',
                'error': 'Email delivery failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error generating OTP for {email}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to generate OTP. Please try again.',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def verify_otp(request):
    """
    Verify OTP code and return account status
    
    Request body:
    {
        "email": "user@example.com",
        "otp_code": "123456"
    }
    
    Response:
    {
        "success": true/false,
        "message": "Verification message",
        "account_status": "new" | "incomplete" | "finished",
        "email": "user@example.com",
        "user_id": 123 (if exists),
        "next_action": "create_profile" | "complete_profile" | "login"
    }
    """
    try:
        email = request.data.get('email')
        otp_code = request.data.get('otp_code')
        
        if not email or not otp_code:
            return Response({
                'success': False,
                'message': 'Email and OTP code are required',
                'account_status': None
            }, status=status.HTTP_400_BAD_REQUEST)

        # Find the latest valid OTP for this email
        otp_instance = OTP.objects.filter(
            email=email,
            is_used=False,
            is_verified=False
        ).order_by('-created_at').first()

        if not otp_instance:
            return Response({
                'success': False,
                'message': 'No valid OTP found. Please request a new one.',
                'account_status': None,
                'require_new_otp': True
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if OTP has expired
        if otp_instance.is_expired():
            return Response({
                'success': False,
                'message': 'OTP has expired. Please request a new one.',
                'account_status': None,
                'require_new_otp': True
            }, status=status.HTTP_400_BAD_REQUEST)

        # Increment attempt count
        otp_instance.attempts += 1
        otp_instance.save()

        # Check if max attempts reached
        if otp_instance.attempts > otp_instance.max_attempts:
            otp_instance.is_used = True
            otp_instance.save()
            return Response({
                'success': False,
                'message': 'Too many attempts. Please request a new OTP.',
                'account_status': None,
                'require_new_otp': True
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verify OTP code
        if otp_instance.otp_code != otp_code:
            attempts_remaining = otp_instance.max_attempts - otp_instance.attempts
            return Response({
                'success': False,
                'message': 'Invalid OTP code',
                'account_status': None,
                'attempts_remaining': attempts_remaining
            }, status=status.HTTP_400_BAD_REQUEST)

        # OTP is valid - mark as used
        otp_instance.is_verified = True
        otp_instance.is_used = True
        otp_instance.save()

        # Determine account status
        try:
            user = User.objects.get(email=email)
            
            # Check if profile is complete using the new method
            if user.profile_completed and user.is_profile_complete():
                account_status = "finished"
                next_action = "login"
                message = "Email verified! Your profile is complete."
            else:
                account_status = "incomplete"
                next_action = "complete_profile"
                message = "Email verified! Please complete your profile."
                
            return Response({
                'success': True,
                'message': message,
                'account_status': account_status,
                'email': email,
                'user_id': user.id,
                'next_action': next_action
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            # New user
            return Response({
                'success': True,
                'message': 'Email verified! Please create your profile.',
                'account_status': 'new',
                'email': email,
                'user_id': None,
                'next_action': 'create_profile'
            }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error verifying OTP for {email}: {str(e)}")
        return Response({
            'success': False,
            'message': 'Failed to verify OTP. Please try again.',
            'account_status': None,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)