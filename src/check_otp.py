"""
Check the latest OTP in the database
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/Users/lbz/Documents/ShareHolder/searcherlist/searcher-backend')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'searcher_project.settings')
django.setup()

from users.models import OTP

# Get the latest OTP
latest_otp = OTP.objects.filter(email='lbzuluagag+test@gmail.com').order_by('-created_at').first()

if latest_otp:
    print(f"Email: {latest_otp.email}")
    print(f"OTP Code: {latest_otp.code}")
    print(f"Attempts: {latest_otp.attempts}")
    print(f"Is Used: {latest_otp.is_used}")
    print(f"Created: {latest_otp.created_at}")
    print(f"Expires: {latest_otp.expires_at}")
else:
    print("No OTP found for lbzuluagag+test@gmail.com")