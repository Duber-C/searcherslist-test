from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending OTP and other emails"""

    @staticmethod
    def send_otp_email(email, otp_code, user_exists=False):
        """Send OTP email to user"""
        try:
            if user_exists:
                subject = "Your Sign-In Code - BuyerProfile"
                message = f"""
Hello!

Here's your sign-in code for BuyerProfile:

{otp_code}

This code will expire in 10 minutes.

If you didn't request this code, please ignore this email.

Best regards,
BuyerProfile Team
                """
            else:
                subject = "Welcome to BuyerProfile - Verify Your Email"
                message = f"""
Welcome to BuyerProfile!

Here's your verification code to get started:

{otp_code}

This code will expire in 10 minutes. After verification, you'll be able to create your buyer profile.

If you didn't sign up for BuyerProfile, please ignore this email.

Best regards,
BuyerProfile Team
                """

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )

            logger.info(f"OTP email sent successfully to {email}")
            return True, "Email sent successfully"

        except Exception as e:
            logger.error(f"Failed to send OTP email to {email}: {str(e)}")
            return False, f"Failed to send email: {str(e)}"

    @staticmethod
    def send_welcome_email(user):
        """Send welcome email after profile creation"""
        try:
            subject = "Welcome to BuyerProfile!"
            message = f"""
Hello {user.first_name}!

Welcome to BuyerProfile! Your account has been successfully created.

Here are your profile details:
- Name: {user.first_name} {user.last_name}
- Email: {user.email}
- Phone: {user.phone_number}
- Location: {user.city}, {user.state}, {user.country}

You can now sign in to your dashboard and manage your buyer profile.

Best regards,
BuyerProfile Team
            """

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,  # Don't fail registration if welcome email fails
            )

            logger.info(f"Welcome email sent to {user.email}")
            return True, "Welcome email sent"

        except Exception as e:
            logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
            return False, f"Failed to send welcome email: {str(e)}"

    @staticmethod
    def send_support_ticket_email(subject, requester_email, message, ticket_id=None, source=None):
        """
        Send a support ticket notification to the support inbox.

        NOTE: We use EmailMessage instead of send_mail() because some Django/mail
        setups do not accept `reply_to` as a kwarg on send_mail().
        """
        try:
            support_to = getattr(settings, "SUPPORT_INBOX_EMAIL", settings.DEFAULT_FROM_EMAIL)

            full_subject = subject
            if ticket_id:
                full_subject = f"{subject} [TICKET-{ticket_id}]"

            body = f"""
New support request

Ticket: {ticket_id or "n/a"}
Source: {source or "n/a"}
From: {requester_email}

Message:
{message}
            """.strip()

            email = EmailMessage(
                subject=full_subject,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[support_to],
                reply_to=[requester_email],  # so you can reply directly to the user
            )
            email.send(fail_silently=False)

            logger.info(f"Support ticket email sent. ticket_id={ticket_id} from={requester_email}")
            return True, "Support email sent"
        except Exception as e:
            logger.error(f"Failed to send support ticket email: {str(e)}")
            return False, f"Failed to send support email: {str(e)}"