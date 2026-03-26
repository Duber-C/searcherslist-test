import logging

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from users.models.support import SupportTicket
from users.services.email import EmailService


logger = logging.getLogger(__name__)


@api_view(["POST"])
def create_support_ticket(request):
    """
    Create a support ticket and email support.

    Expected JSON:
    {
      "subject": "Login issues",
      "email": "user@example.com",
      "message": "I can't log in...",
      "source": "signin"
    }
    """
    subject = (request.data.get("subject") or "Login issues").strip()
    email = (request.data.get("email") or "").strip().lower()
    message = (request.data.get("message") or "").strip()
    source = (request.data.get("source") or "signin").strip()

    if not email:
        return Response({"success": False, "message": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
    if not message:
        return Response({"success": False, "message": "Message is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        ticket = SupportTicket.objects.create(
            subject=subject[:200],
            requester_email=email,
            message=message,
            source=source[:50],
        )

        ok, msg = EmailService.send_support_ticket_email(
            subject=ticket.subject,
            requester_email=ticket.requester_email,
            message=ticket.message,
            ticket_id=ticket.id,
            source=ticket.source,
        )

        if not ok:
            # Keep the ticket, but report email failure
            return Response(
                {"success": False, "message": msg, "ticket_id": ticket.id},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"success": True, "message": "Support request sent", "ticket_id": ticket.id},
            status=status.HTTP_201_CREATED,
        )
    except Exception as e:
        logger.error(f"Support ticket creation failed: {str(e)}")
        return Response(
            {"success": False, "message": "Failed to create support ticket"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
