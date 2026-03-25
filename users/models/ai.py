from django.db import models

from users.models.user import User


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
