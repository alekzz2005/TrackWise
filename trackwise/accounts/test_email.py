# test_email.py
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trackwise.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

print(f"RESEND_API_KEY: {settings.RESEND_API_KEY[:10]}..." if settings.RESEND_API_KEY else "NOT SET")
print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")

try:
    send_mail(
        'Test from script',
        'If you get this, email works!',
        settings.DEFAULT_FROM_EMAIL,
        ['your-email@gmail.com'],  # Change to your email
    )
    print("✅ Email sent!")
except Exception as e:
    print(f"❌ Error: {e}")