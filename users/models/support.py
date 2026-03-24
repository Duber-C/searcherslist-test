from django.db import models


class SupportTicket(models.Model):
    STATUS_OPEN = "open"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_CLOSED, "Closed"),
    ]

    subject = models.CharField(max_length=200, default="Login issues")
    requester_email = models.EmailField()
    message = models.TextField()
    source = models.CharField(max_length=50, blank=True, default="signin")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.status}] {self.subject} - {self.requester_email}"
