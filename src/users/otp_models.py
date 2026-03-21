from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import random
import string
from datetime import timedelta

User = get_user_model()


class OTP(models.Model):
    """
    OTP model for email verification
    """
    email = models.EmailField()
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    is_used = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    
    # Track if user exists or needs to be created
    user_exists = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        db_table = 'users_otp'
        verbose_name = 'OTP'
        verbose_name_plural = 'OTPs'
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        # Generate OTP code if not provided
        if not self.otp_code:
            self.otp_code = self.generate_otp()
        
        # Set expiration time (10 minutes from creation)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        
        # Check if user exists
        try:
            user = User.objects.get(email=self.email)
            self.user_exists = True
            self.user = user
        except User.DoesNotExist:
            self.user_exists = False
            self.user = None
        
        super().save(*args, **kwargs)
    
    def generate_otp(self):
        """Generate a 6-digit OTP code"""
        return ''.join(random.choices(string.digits, k=6))
    
    def is_expired(self):
        """Check if OTP is expired"""
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Check if OTP is valid (not expired, not used, attempts not exceeded)"""
        return (
            not self.is_expired() and 
            not self.is_used and 
            self.attempts < self.max_attempts
        )
    
    def verify(self, code):
        """Verify OTP code"""
        self.attempts += 1
        
        if self.attempts >= self.max_attempts:
            self.save()
            return False, "Maximum attempts exceeded"
        
        if self.is_expired():
            self.save()
            return False, "OTP has expired"
        
        if self.is_used:
            self.save()
            return False, "OTP has already been used"
        
        if self.otp_code != code:
            self.save()
            return False, "Invalid OTP code"
        
        # OTP is valid
        self.is_verified = True
        self.is_used = True
        self.save()
        return True, "OTP verified successfully"
    
    def __str__(self):
        status = "Verified" if self.is_verified else "Pending"
        user_status = "Existing User" if self.user_exists else "New User"
        return f"{self.email} - {self.otp_code} ({status}) - {user_status}"
    
    @classmethod
    def create_otp(cls, email):
        """Create a new OTP for an email address"""
        # Deactivate any existing unused OTPs for this email
        cls.objects.filter(email=email, is_used=False).update(is_used=True)
        
        # Create new OTP
        otp = cls.objects.create(email=email)
        return otp
    
    @classmethod
    def get_valid_otp(cls, email):
        """Get the most recent valid OTP for an email"""
        try:
            otp = cls.objects.filter(
                email=email,
                is_used=False
            ).order_by('-created_at').first()
            
            if otp and otp.is_valid():
                return otp
            return None
        except cls.DoesNotExist:
            return None