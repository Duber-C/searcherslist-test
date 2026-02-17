from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid
import random
import string
import re


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
    
    # Professional fields
    value_proposition = models.TextField(blank=True, null=True, help_text="What unique value do you bring?")
    areas_of_expertise = models.TextField(blank=True, null=True, help_text="Your key areas of expertise")
    investment_experience = models.CharField(max_length=100, blank=True, null=True, help_text="Years of investment experience")
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

        # Detect previous published state to know if we just published
        previous_published = False
        if self.pk:
            try:
                prev = User.objects.get(pk=self.pk)
                previous_published = bool(prev.published)
            except User.DoesNotExist:
                previous_published = False

        super().save(*args, **kwargs)

        # If the profile is published and we don't have a public token yet, generate one.
        # If the profile was previously published but is now unpublished, remove the token.
        if self.published and not self.public_token:
            self.public_token = uuid.uuid4()
            super().save(update_fields=['public_token'])

        # If the profile was previously published and now is not, clear the token
        if not self.published and previous_published and self.public_token:
            self.public_token = None
            super().save(update_fields=['public_token'])

    class Meta:
        db_table = 'users_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'


# Import OTP model
from .otp_models import OTP


# AI Models for managing AI services, agents, and interaction logs
class AIService(models.Model):
    """
    Model to store AI service configurations (GPT, Claude, etc.)
    """
    SERVICE_CHOICES = [
        ('openai', 'OpenAI (GPT)'),
        ('anthropic', 'Anthropic (Claude)'),
        ('google', 'Google (Gemini)'),
        ('azure', 'Azure OpenAI'),
        ('local', 'Local Model'),
        ('custom', 'Custom API'),
    ]
    
    name = models.CharField(max_length=100, help_text="Display name for the AI service")
    service_type = models.CharField(max_length=20, choices=SERVICE_CHOICES, help_text="Type of AI service")
    description = models.TextField(blank=True, help_text="Description of this AI service")
    api_endpoint = models.URLField(blank=True, help_text="API endpoint URL (if custom)")
    model_name = models.CharField(max_length=100, help_text="Model name (e.g., gpt-4, claude-3-sonnet)")
    api_key_name = models.CharField(max_length=50, default='OPENAI_API_KEY', help_text="Environment variable name for API key")
    
    # Configuration
    max_tokens = models.IntegerField(default=4000, help_text="Maximum tokens for responses")
    temperature = models.FloatField(default=0.1, help_text="Temperature for response randomness (0.0-1.0)")
    
    # Pricing (for cost tracking)
    input_cost_per_1k_tokens = models.DecimalField(max_digits=10, decimal_places=6, default=0.0, help_text="Cost per 1K input tokens in USD")
    output_cost_per_1k_tokens = models.DecimalField(max_digits=10, decimal_places=6, default=0.0, help_text="Cost per 1K output tokens in USD")
    
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False, help_text="Use this as the default service")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_default', 'name']
        verbose_name = "AI Service"
        verbose_name_plural = "AI Services"
    
    def __str__(self):
        return f"{self.name} ({self.model_name})"
    
    def save(self, *args, **kwargs):
        # Ensure only one default service
        if self.is_default:
            AIService.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class AIAgent(models.Model):
    """
    Model to store AI agents with their specific prompts and configurations
    """
    AGENT_TYPES = [
        ('profile_extraction', 'Profile Extraction'),
        ('content_generation', 'Content Generation'),
        ('data_analysis', 'Data Analysis'),
        ('chat_assistant', 'Chat Assistant'),
        ('custom', 'Custom Agent'),
    ]
    
    name = models.CharField(max_length=100, help_text="Name of the AI agent")
    agent_type = models.CharField(max_length=30, choices=AGENT_TYPES, help_text="Type of agent")
    description = models.TextField(blank=True, help_text="Description of what this agent does")
    
    # Prompt configuration
    system_prompt = models.TextField(help_text="System prompt that defines the agent's role and behavior")
    user_prompt_template = models.TextField(help_text="Template for user prompts (can include variables like {text})")
    
    # AI Service configuration
    ai_service = models.ForeignKey(AIService, on_delete=models.CASCADE, help_text="Which AI service to use")
    
    # Override service settings if needed
    custom_temperature = models.FloatField(null=True, blank=True, help_text="Override temperature for this agent")
    custom_max_tokens = models.IntegerField(null=True, blank=True, help_text="Override max tokens for this agent")
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['agent_type', 'name']
        verbose_name = "AI Agent"
        verbose_name_plural = "AI Agents"
    
    def __str__(self):
        return f"{self.name} ({self.get_agent_type_display()})"
    
    def get_effective_temperature(self):
        """Get the temperature to use (custom or from AI service)"""
        return self.custom_temperature if self.custom_temperature is not None else self.ai_service.temperature
    
    def get_effective_max_tokens(self):
        """Get the max tokens to use (custom or from AI service)"""
        return self.custom_max_tokens if self.custom_max_tokens is not None else self.ai_service.max_tokens


class AIInteractionLog(models.Model):
    """
    Model to log all AI interactions for monitoring, debugging, and cost tracking
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('error', 'Error'),
        ('timeout', 'Timeout'),
    ]
    
    # Request context
    agent = models.ForeignKey(AIAgent, on_delete=models.CASCADE, help_text="Which agent was used")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, help_text="User who triggered the request")
    session_id = models.CharField(max_length=100, blank=True, help_text="Session identifier for grouping related requests")
    
    # Request data
    input_text = models.TextField(help_text="Input text sent to AI")
    system_prompt_used = models.TextField(help_text="System prompt that was used")
    user_prompt_used = models.TextField(help_text="User prompt that was sent")
    
    # Request metadata
    temperature_used = models.FloatField(help_text="Temperature setting used")
    max_tokens_used = models.IntegerField(help_text="Max tokens setting used")
    model_used = models.CharField(max_length=100, help_text="Model name that was used")
    
    # Response data
    response_text = models.TextField(blank=True, help_text="Raw response from AI")
    parsed_response = models.JSONField(default=dict, help_text="Parsed/structured response data")
    
    # Execution details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, help_text="Error message if request failed")
    
    # Timing and cost
    request_timestamp = models.DateTimeField(auto_now_add=True)
    response_timestamp = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.FloatField(null=True, blank=True, help_text="Time taken for the request")
    
    # Token usage
    input_tokens = models.IntegerField(null=True, blank=True, help_text="Number of input tokens used")
    output_tokens = models.IntegerField(null=True, blank=True, help_text="Number of output tokens generated")
    total_tokens = models.IntegerField(null=True, blank=True, help_text="Total tokens used")
    
    # Cost calculation
    input_cost = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True, help_text="Cost of input tokens")
    output_cost = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True, help_text="Cost of output tokens")
    total_cost = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True, help_text="Total cost of the request")
    
    # Additional metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    additional_metadata = models.JSONField(default=dict, help_text="Any additional metadata")
    
    class Meta:
        ordering = ['-request_timestamp']
        verbose_name = "AI Interaction Log"
        verbose_name_plural = "AI Interaction Logs"
        indexes = [
            models.Index(fields=['agent', 'request_timestamp']),
            models.Index(fields=['user', 'request_timestamp']),
            models.Index(fields=['status', 'request_timestamp']),
        ]
    
    def __str__(self):
        return f"{self.agent.name} - {self.request_timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {self.status}"
    
    def calculate_cost(self):
        """Calculate and update cost based on token usage and AI service pricing"""
        if self.input_tokens and self.output_tokens:
            from decimal import Decimal
            ai_service = self.agent.ai_service
            self.input_cost = (Decimal(str(self.input_tokens)) / Decimal('1000')) * ai_service.input_cost_per_1k_tokens
            self.output_cost = (Decimal(str(self.output_tokens)) / Decimal('1000')) * ai_service.output_cost_per_1k_tokens
            self.total_cost = self.input_cost + self.output_cost
            self.save(update_fields=['input_cost', 'output_cost', 'total_cost'])
    
    def mark_completed(self, response_text, parsed_response=None, token_usage=None, error=None):
        """Mark the interaction as completed with response data"""
        from django.utils import timezone
        
        self.response_timestamp = timezone.now()
        if self.request_timestamp:
            self.duration_seconds = (self.response_timestamp - self.request_timestamp).total_seconds()
        
        if error:
            self.status = 'error'
            self.error_message = str(error)
        else:
            self.status = 'success'
            self.response_text = response_text
            if parsed_response:
                self.parsed_response = parsed_response
        
        if token_usage:
            self.input_tokens = token_usage.get('prompt_tokens', 0)
            self.output_tokens = token_usage.get('completion_tokens', 0)
            self.total_tokens = token_usage.get('total_tokens', 0)
        
        self.save()
        
        # Calculate cost if we have token usage
        if self.input_tokens and self.output_tokens:
            self.calculate_cost()


class Question(models.Model):
    """
    Dynamic questionnaire questions model for buyer profile creation
    """
    QUESTION_TYPES = [
        ('text', 'Text Input'),
        ('textarea', 'Text Area'),
        ('select', 'Select Dropdown'),
    ]
    
    id = models.CharField(max_length=100, primary_key=True, help_text="Unique identifier for the question")
    text = models.TextField(help_text="The question text displayed to users")
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='text')
    required = models.BooleanField(default=False, help_text="Whether this question must be answered")
    placeholder = models.CharField(max_length=500, blank=True, help_text="Placeholder text for input fields")
    options = models.JSONField(blank=True, null=True, help_text="Options for select type questions (list of strings)")
    order = models.PositiveIntegerField(help_text="Display order of the question")
    is_active = models.BooleanField(default=True, help_text="Whether this question is currently active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order']
        
    def __str__(self):
        return f"{self.order}. {self.text[:50]}{'...' if len(self.text) > 50 else ''}"


import uuid
from datetime import timedelta
from django.utils import timezone

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


class OTPVerification(models.Model):
    """
    Model for storing OTP codes for email verification
    """
    email = models.EmailField()
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    used_at = models.DateTimeField(blank=True, null=True)
    signed_link = models.ForeignKey(Signed_links, on_delete=models.CASCADE, related_name='otp_verifications', null=True, blank=True)
    
    class Meta:
        verbose_name = "OTP Verification"
        verbose_name_plural = "OTP Verifications"
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.otp_code:
            # Generate 6-digit OTP
            self.otp_code = ''.join(random.choices(string.digits, k=6))
        if not self.expires_at:
            # Set expiry to 10 minutes from creation
            self.expires_at = timezone.now() + timezone.timedelta(minutes=10)
        super().save(*args, **kwargs)
    
    def is_valid(self):
        """Check if the OTP is still valid (not expired and not used)"""
        return not self.used and timezone.now() < self.expires_at
    
    def mark_as_used(self):
        """Mark the OTP as used"""
        self.used = True
        self.used_at = timezone.now()
        self.save()
    
    def __str__(self):
        status = "Used" if self.used else ("Expired" if timezone.now() > self.expires_at else "Valid")
        return f"{self.email} - {self.otp_code} - {status}"
