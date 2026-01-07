from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .otp_models import OTP
import re

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration with all profile fields
    """
    password = serializers.CharField(write_only=True, required=False)
    confirm_password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'confirm_password',
            'first_name', 'last_name', 'phone_number', 
            'country', 'city', 'state', 'linkedin_url',
            'resume', 'buyer_profile', 'background',
            'value_proposition', 'areas_of_expertise', 'investment_experience',
            'deal_size_preference', 'industry_focus', 'geographic_focus',
            'current_role', 'company', 'years_experience',
            'education', 'certifications', 'achievements', 'website', 'bio', 'skills', 'languages'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
            'phone_number': {'required': False},
            'country': {'required': False},
            'city': {'required': False},
            'state': {'required': False},
            'linkedin_url': {'required': False},
            'background': {'required': False},
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If this is an update (instance exists), make most fields optional
        if self.instance:
            for field_name, field in self.fields.items():
                if field_name not in ['email']:  # Keep email as always required
                    field.required = False
    
    def validate_email(self, value):
        """Validate email is unique (unless email is already verified or updating existing user)"""
        # Check if this is for a verified email or updating existing user
        if self.context.get('email_verified', False) or self.context.get('updating_existing', False):
            return value
            
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_username(self, value):
        """Validate username is unique (unless updating existing user)"""
        # If no value provided, skip validation
        if not value:
            return value
            
        # If updating existing user and username hasn't changed, allow it
        if self.instance and self.instance.username == value:
            return value
            
        # If updating existing user with context flag, be more lenient
        if self.context.get('updating_existing', False):
            # Still check for uniqueness but exclude current instance
            if self.instance:
                if User.objects.filter(username=value).exclude(id=self.instance.id).exists():
                    raise serializers.ValidationError("A user with that username already exists.")
            else:
                if User.objects.filter(username=value).exists():
                    raise serializers.ValidationError("A user with that username already exists.")
            return value
            
        # For new users, check normal uniqueness
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value
    
    def validate_phone_number(self, value):
        """Validate phone number format"""
        if value and not re.match(r'^\+?1?\d{9,15}$', value):
            raise serializers.ValidationError(
                "Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        return value
    
    def validate_linkedin_url(self, value):
        """Validate LinkedIn URL"""
        if value and 'linkedin.com' not in value.lower():
            raise serializers.ValidationError("Please enter a valid LinkedIn profile URL.")
        return value
    
    def validate_background(self, value):
        """Validate background has minimum length"""
        if value and len(value.strip()) < 50:
            raise serializers.ValidationError("Please provide at least 50 characters describing your background.")
        return value
    
    def validate(self, attrs):
        """Custom validation for password confirmation"""
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')
        
        # If password is provided, validate it
        if password:
            if password != confirm_password:
                raise serializers.ValidationError("Password and confirm password do not match.")
            
            # Validate password strength
            validate_password(password)
        else:
            # Generate username from email if no password provided (for social auth, etc.)
            if attrs.get('email'):
                attrs['username'] = attrs['email'].split('@')[0]
        
        return attrs
    
    def create(self, validated_data):
        """Create user with validated data"""
        # Remove confirm_password from validated_data
        validated_data.pop('confirm_password', None)
        
        password = validated_data.pop('password', None)
        
        # Generate username from email if not provided
        if not validated_data.get('username') and validated_data.get('email'):
            base_username = validated_data['email'].split('@')[0]
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            validated_data['username'] = username
        
        # Create user
        user = User.objects.create(**validated_data)
        
        # Set password if provided
        if password:
            user.set_password(password)
            user.save()
        
        return user
    
    def update(self, instance, validated_data):
        """Update existing user with validated data"""
        # Remove confirm_password from validated_data
        validated_data.pop('confirm_password', None)
        
        password = validated_data.pop('password', None)
        
        # NEVER update username for existing users - completely remove it
        validated_data.pop('username', None)
        print(f"DEBUG: Removed username from validated_data during update to prevent constraint violations")
        
        # Update user fields
        for attr, value in validated_data.items():
            if value is not None and value != '':  # Only update non-empty values
                setattr(instance, attr, value)
        
        # Set password if provided
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile data (read operations)
    """
    resume_url = serializers.SerializerMethodField()
    buyer_profile_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'country', 'city', 'state', 'linkedin_url',
            'resume', 'buyer_profile', 'resume_url', 'buyer_profile_url',
            'resume_upload', 'existing_buyer_profile',
            'background', 'created_at', 'updated_at',
            'value_proposition', 'areas_of_expertise', 'investment_experience',
            'deal_size_preference', 'industry_focus', 'geographic_focus',
            'current_role', 'company', 'years_experience', 'profile_completed',
            'education', 'professional_experience', 'certifications', 'achievements', 'website', 'bio', 'skills', 'languages'
        ]
        read_only_fields = ['id', 'username', 'created_at', 'updated_at']
    
    def get_resume_url(self, obj):
        """Get the URL for the resume file if it exists"""
        if obj.resume:
            try:
                return obj.resume.url
            except:
                return None
        return None
    
    def get_buyer_profile_url(self, obj):
        """Get the URL for the buyer profile file if it exists"""
        if obj.buyer_profile:
            try:
                return obj.buyer_profile.url
            except:
                return None
        return None


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile
    """
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone_number', 
            'country', 'city', 'state', 'linkedin_url',
            'resume', 'buyer_profile', 'background',
            'value_proposition', 'areas_of_expertise', 'investment_experience',
            'deal_size_preference', 'industry_focus', 'geographic_focus',
            'current_role', 'company', 'years_experience',
            'education', 'professional_experience', 'certifications', 'achievements', 'website', 'bio', 'skills', 'languages'
        ]
    
    def validate_phone_number(self, value):
        """Validate phone number format"""
        if value and not re.match(r'^\+?1?\d{9,15}$', value):
            raise serializers.ValidationError(
                "Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        return value
    
    def validate_linkedin_url(self, value):
        """Validate LinkedIn URL"""
        if value and 'linkedin.com' not in value.lower():
            raise serializers.ValidationError("Please enter a valid LinkedIn profile URL.")
        return value
    
    def validate_background(self, value):
        """Validate background has minimum length"""
        if value and len(value.strip()) < 50:
            raise serializers.ValidationError("Please provide at least 50 characters describing your background.")
        return value

class SendOTPSerializer(serializers.Serializer):
    """Serializer for sending OTP"""
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """Validate email format"""
        return value.lower().strip()


class VerifyOTPSerializer(serializers.Serializer):
    """Serializer for verifying OTP"""
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6, min_length=6)
    
    def validate_email(self, value):
        """Validate email format"""
        return value.lower().strip()
    
    def validate_otp_code(self, value):
        """Validate OTP code format"""
        if not value.isdigit():
            raise serializers.ValidationError("OTP code must contain only digits.")
        return value


class OTPSerializer(serializers.ModelSerializer):
    """Serializer for OTP model"""
    class Meta:
        model = OTP
        fields = [
            'id', 'email', 'created_at', 'expires_at', 
            'is_verified', 'is_used', 'attempts', 'user_exists'
        ]
        read_only_fields = ['id', 'created_at', 'expires_at', 'is_verified', 'is_used', 'attempts', 'user_exists']
