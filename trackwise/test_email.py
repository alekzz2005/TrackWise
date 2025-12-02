# test_email.py
import os
import sys

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trackwise.settings')

import django
django.setup()

from django.core.mail import send_mail
from django.conf import settings

print("="*60)
print("EMAIL CONFIGURATION TEST")
print("="*60)

# Check settings
print(f"DEBUG Mode: {settings.DEBUG}")
print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

# Check if Resend API key is loaded
if hasattr(settings, 'RESEND_API_KEY'):
    resend_key = settings.RESEND_API_KEY
    if resend_key:
        print(f"✅ RESEND_API_KEY is SET (first 10 chars): {resend_key[:10]}...")
    else:
        print("❌ RESEND_API_KEY is EMPTY")
else:
    print("❌ RESEND_API_KEY not found in settings")

print("-"*60)

# Try to send a test email
test_email = "cararagtrisharaye@gmail.com"  # CHANGE THIS TO YOUR EMAIL
print(f"Attempting to send test email to: {test_email}")

try:
    result = send_mail(
        subject='✅ TrackWise Email Test',
        message='Congratulations! Your TrackWise email configuration is working correctly!\n\nIf you received this email, the OTP system will work properly.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[test_email],
        fail_silently=False,
    )
    print(f"✅ SUCCESS! Email sent. Result: {result}")
    print(f"📧 Email should arrive at: {test_email}")
    print("💡 Check your inbox (and spam folder)")
    
except Exception as e:
    print(f"❌ FAILED to send email: {str(e)}")
    print("\nTROUBLESHOOTING:")
    print("1. Check if .env file exists in the same folder as manage.py")
    print("2. Make sure .env contains: RESEND_API_KEY=re_your_key_here")
    print("3. Verify your Resend API key at https://resend.com")
    print("4. Restart Django after creating .env file")
    print("5. Try setting environment variable directly:")
    print("   Windows CMD: set RESEND_API_KEY=re_your_key_here")
    print("   Then run: python manage.py runserver")

print("="*60)