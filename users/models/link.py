import uuid
from datetime import  timedelta

from django.utils import timezone
from django.db import models


class Signed_links(models.Model):
    """
    Model for secure signed URLs that provide access to the frontend
    """
    email = models.EmailField()
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    used_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Signed Link"
        verbose_name_plural = "Signed Links"
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Set expiry to 24 hours from creation
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)
    
    def is_valid(self):
        """Check if the link is still valid (not expired and not used)"""
        return not self.used and timezone.now() < self.expires_at
    
    def mark_as_used(self):
        """Mark the link as used"""
        self.used = True
        self.used_at = timezone.now()
        self.save()
    
    def __str__(self):
        status = "Used" if self.used else ("Expired" if timezone.now() > self.expires_at else "Valid")
        return f"{self.email} - {status} - {self.token}"

