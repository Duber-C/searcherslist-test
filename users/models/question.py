from django.db import models

class Question(models.Model):
    """
    Dynamic questionnaire questions model for buyer profile creation
    """
    QUESTION_TYPES = [
        ('text', 'Text Input'),
        ('textarea', 'Text Area'),
        ('select', 'Select Dropdown'),
        ('radio', 'Radio / Single Select'),
        ('checkbox', 'Single Checkbox'),
        ('multiselect', 'Multi Select'),
        ('checkbox_group', 'Checkbox Group / Multi Select'),
        ('custom', 'Custom (frontend-managed)'),
        ('composite', 'Composite / Group of sub-questions'),
    ]
    
    id = models.CharField(max_length=100, primary_key=True, help_text="Unique identifier for the question")
    text = models.TextField(help_text="The question text displayed to users")
    question_type = models.CharField(max_length=30, choices=QUESTION_TYPES, default='text', help_text="Type of question to control frontend rendering")
    required = models.BooleanField(default=False, help_text="Whether this question must be answered")
    placeholder = models.CharField(max_length=500, blank=True, help_text="Placeholder text for input fields")
    # Short subtitle/description shown below the question title (separate from placeholder)
    subtitle = models.TextField(blank=True, help_text="Short subtitle or description for the question")
    # Options for select/radio/checkbox group; stored as a list of option objects or strings
    options = models.JSONField(default=list, blank=True, help_text="Options for select/radio/checkbox questions (list)")
    # Examples to show under the question (e.g., example business types)
    examples = models.JSONField(default=list, blank=True, help_text="Short example values to display for this question")
    # helper text to show under the question
    helper_text = models.CharField(default="", blank=True, help_text="Short help description")
    # Arbitrary extra data for highly-customized questions (rendered/used by frontend component)
    extra = models.JSONField(default=dict, blank=True, help_text="Additional JSON metadata for custom question components")
    # Frontend component identifier (optional): allows explicit mapping to a UI component
    component = models.CharField(max_length=100, blank=True, null=True, help_text="Optional frontend component name/identifier")
    # Validation metadata (min/max, regex, allowed values, etc.) consumed by frontend and backend
    validation = models.JSONField(default=dict, blank=True, help_text="Validation rules and metadata for this question")
    order = models.PositiveIntegerField(help_text="Display order of the question")
    # Questionnaire page number (allows splitting questions across multiple pages)
    page = models.PositiveIntegerField(default=1, help_text="Questionnaire page number (1,2,...)")
    is_active = models.BooleanField(default=True, help_text="Whether this question is currently active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order']
        
    def __str__(self):
        return f"{self.order}. {self.text[:50]}{'...' if len(self.text) > 50 else ''}"
