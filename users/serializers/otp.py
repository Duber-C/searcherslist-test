from rest_framework import serializers

from users.models.otp import OTP


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


