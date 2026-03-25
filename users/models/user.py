import uuid
import random
import string
import re
from datetime import timedelta

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    """
    Extended User model with additional fields for searcher profiles
    """
    # Phone number - will be cleaned and validated in save method
    phone_number = models.CharField(max_length=17, blank=True, null=True)
    
    # Location fields
    country = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    
    # LinkedIn profile
    linkedin_url = models.URLField(blank=True, null=True)
    
    # File uploads
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    buyer_profile = models.FileField(upload_to='buyer_profiles/', blank=True, null=True)
    
    # File content storage (extracted text from uploaded documents)
    resume_upload = models.TextField(blank=True, null=True, help_text="Content extracted from uploaded resume")
    existing_buyer_profile = models.TextField(blank=True, null=True, help_text="Content extracted from uploaded buyer profile")
    linkedin_data = models.JSONField(blank=True, null=True, help_text="Structured LinkedIn profile data")
    
    # Background/overview
    background = models.TextField(blank=True, null=True)
    # Acquisition target: what the user is looking to buy (explicit buyer profile content preferred)
    acquisition_target = models.TextField(blank=True, null=True, help_text="What the user is looking to buy; prefer explicit buyer profile content if uploaded")
    # Target statement: concise 1-sentence target (business type, size, geography)
    target_statement = models.TextField(blank=True, null=True, help_text="Short target statement: 1 sentence with business type, size, geography")
    
    # Professional fields
    value_proposition = models.TextField(blank=True, null=True, help_text="What unique value do you bring?")
    areas_of_expertise = models.TextField(blank=True, null=True, help_text="Your key areas of expertise")
    investment_experience = models.CharField(max_length=500, blank=True, null=True, help_text="Years of investment experience")
    deal_size_preference = models.CharField(max_length=200, blank=True, null=True, help_text="Preferred deal size range")
    industry_focus = models.TextField(blank=True, null=True, help_text="Industries you focus on")
    geographic_focus = models.CharField(max_length=200, blank=True, null=True, help_text="Geographic regions of focus")
    
    # Additional professional info
    current_role = models.CharField(max_length=200, blank=True, null=True)
    company = models.CharField(max_length=200, blank=True, null=True)
    years_experience = models.CharField(max_length=50, blank=True, null=True)
    
    # Education & Certification (structured as lists)
    education = models.JSONField(
        default=list,
        blank=True,
        help_text="List of education entries: [{'school': str, 'degree': str, 'field': str, 'years': str, 'description': str}, ...]"
    )
    professional_experience = models.JSONField(
        default=list,
        blank=True,
        help_text="List of work experience: [{'company': str, 'title': str, 'duration': str, 'description': str, 'achievements': str}, ...]"
    )
    certifications = models.TextField(blank=True, null=True, help_text="Professional certifications")
    achievements = models.TextField(blank=True, null=True, help_text="Notable achievements and awards")
    
    # Additional profile fields
    website = models.URLField(blank=True, null=True, help_text="Personal or company website")
    bio = models.TextField(blank=True, null=True, help_text="Professional bio/summary")
    skills = models.TextField(blank=True, null=True, help_text="Key skills and competencies")
    languages = models.CharField(max_length=200, blank=True, null=True, help_text="Languages spoken")
    
    # Profile completion status
    profile_completed = models.BooleanField(default=False)
    # Whether the user has published their public profile
    published = models.BooleanField(default=False)

    # Opaque public token for building public profile URLs (UUID)
    # Generated when a user publishes their profile; nullable for existing users
    public_token = models.UUIDField(null=True, blank=True, unique=True, editable=False)
    # API bearer token for programmatic auth (do not expose publicly)
    api_token = models.CharField(max_length=64, null=True, blank=True, unique=True, editable=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Raw structured questionnaire answers stored after profile creation/processing
    questionnaire_answers = models.JSONField(default=dict, blank=True, help_text="Structured questionnaire answers (may include option titles and subtitles)")
    
    token_create_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when api_token was first created",
    )

    def ensure_public_token(self, save=True):
        print("Ensuring public token for user:", self.email)
        """
        Ensure public_token exists.
        If token_create_at is NULL, set it once the first time we hit this method.
        """
        changed_fields = []

        if self.token_create_at is None:
            print("Setting token_create_at for user:", self.email)
            self.token_create_at = timezone.now()
            changed_fields.append("token_create_at")

        if not self.public_token:
            self.public_token = uuid.uuid4()
            changed_fields.append("public_token")

        if changed_fields:
            self.save(update_fields=changed_fields)
        print("token create at:", self.token_create_at, "public token:", self.public_token)
        return self.public_token
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"
    
    def is_profile_complete(self):
        """Check if all required profile fields are filled"""
        # Only check core required fields - new professional fields are optional
        required_fields = [
            'first_name', 'last_name', 'phone_number', 
            'country', 'city', 'state', 'linkedin_url', 'background'
        ]
        return all(getattr(self, field) for field in required_fields)
    
    def mark_profile_complete(self):
        """Mark profile as completed if all required fields are filled"""
        if self.is_profile_complete():
            self.profile_completed = True
            self.save(update_fields=['profile_completed'])
            return True
        return False
    
    def clean_phone_number(self, phone):
        """Clean and validate phone number"""
        if not phone:
            return ""
        
        # Remove all non-digit characters
        cleaned = re.sub(r'[^\d]', '', phone)
        
        # Add country code if missing (assume US +1)
        if len(cleaned) == 10:
            cleaned = '1' + cleaned
        elif len(cleaned) == 11 and cleaned.startswith('1'):
            pass  # Already has country code
        else:
            # Invalid length, return as-is and let validation fail
            return phone
        
        # Format as +1234567890
        return '+' + cleaned
    
    def clean_url_field(self, url):
        """Clean and validate URL fields"""
        if not url:
            return ""
        
        # Add https:// if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        return url
    
    def save(self, *args, **kwargs):
        """Clean fields before saving"""
        # Clean phone number
        if self.phone_number:
            self.phone_number = self.clean_phone_number(self.phone_number)
        
        # Clean LinkedIn URL
        if self.linkedin_url:
            self.linkedin_url = self.clean_url_field(self.linkedin_url)
        
        # Clean website URL
        if self.website:
            self.website = self.clean_url_field(self.website)
        
        # Persist model first
        super().save(*args, **kwargs)
        
        # If the profile is published and we don't have a public token yet, generate one.
        # Do NOT clear or change the public_token when a profile is unpublished — token persists.
        if self.published and not self.public_token:
            self.public_token = uuid.uuid4()
            super().save(update_fields=['public_token'])

    class Meta:
        db_table = 'users_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

