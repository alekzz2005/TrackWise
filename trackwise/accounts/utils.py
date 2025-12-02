import logging
from django.conf import settings
from infobip_channels.email.channel import EmailChannel
from infobip_api_client.api_client import ApiClient, Configuration

logger = logging.getLogger(__name__)

def send_infobip_email(to_email, subject, html_content, text_content=None):
    """
    Send email using Infobip API
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML content of the email
        text_content: Plain text content (optional)
    
    Returns:
        bool: True if successful, False otherwise
    """
    
    # If no Infobip API key, fall back to Django's send_mail
    if not getattr(settings, 'INFOBIP_API_KEY', None):
        logger.warning("Infobip API key not configured, falling back to Django send_mail")
        from django.core.mail import send_mail
        try:
            send_mail(
                subject=subject,
                message=text_content or html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                html_message=html_content,
                fail_silently=False,
            )
            return True
        except Exception as e:
            logger.error(f"Fallback email sending failed: {str(e)}")
            return False
    
    try:
        # IMPORTANT: For your specific base URL (v35rjm.api.infobip.com)
        # We need to ensure it has the https:// prefix for API calls
        base_url = settings.INFOBIP_BASE_URL
        if not base_url.startswith('http'):
            base_url = f"https://{base_url}"
        
        # Initialize Infobip configuration with your specific base URL
        configuration = Configuration(
            host=base_url,  # This becomes https://v35rjm.api.infobip.com
            api_key_prefix="App",
            api_key=settings.INFOBIP_API_KEY,
        )
        
        api_client = ApiClient(configuration=configuration)
        email_channel = EmailChannel(api_client)
        
        # Prepare the email
        response = email_channel.send_email_message(
            from_email=settings.INFOBIP_SENDER_EMAIL,
            to=[to_email],
            subject=subject,
            html=html_content,
            text=text_content or html_content,
        )
        
        logger.info(f"Infobip email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Infobip email sending failed for {to_email}: {str(e)}")
        
        # Try fallback to SMTP (using the same base URL)
        try:
            from django.core.mail import send_mail
            send_mail(
                subject=subject,
                message=text_content or html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                html_message=html_content,
                fail_silently=True,
            )
            logger.info(f"Fallback SMTP email sent to {to_email}")
            return True
        except Exception as smtp_error:
            logger.error(f"All email methods failed for {to_email}: {smtp_error}")
            return False

def send_verification_email_using_infobip(email, otp_code):
    """
    Send OTP verification email using Infobip
    
    Args:
        email: Recipient email
        otp_code: The OTP code to send
    
    Returns:
        bool: True if successful
    """
    subject = 'Your TrackWise Verification Code'
    
    # HTML email content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #007bff; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ padding: 30px; background-color: #f8f9fa; border-radius: 0 0 8px 8px; }}
            .otp-code {{ font-size: 32px; font-weight: bold; text-align: center; color: #007bff; margin: 30px 0; padding: 20px; background-color: white; border-radius: 8px; border: 2px dashed #007bff; letter-spacing: 5px; }}
            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; text-align: center; }}
            .note {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>TrackWise</h1>
            <p>Email Verification</p>
        </div>
        
        <div class="content">
            <h2>Hello!</h2>
            <p>Thank you for registering with TrackWise. Please use the following verification code to complete your registration:</p>
            
            <div class="otp-code">{otp_code}</div>
            
            <div class="note">
                <strong>Important:</strong> This code will expire in 10 minutes. Please do not share this code with anyone.
            </div>
            
            <p>If you didn't request this verification code, please ignore this email or contact our support team if you have concerns.</p>
            
            <p>Best regards,<br>
            <strong>The TrackWise Team</strong></p>
        </div>
        
        <div class="footer">
            <p>This email was sent to {email} as part of your TrackWise registration.</p>
            <p>© 2024 TrackWise. All rights reserved.</p>
        </div>
    </body>
    </html>
    """
    
    # Plain text content
    text_content = f"""
    Welcome to TrackWise!
    
    Your verification code is: {otp_code}
    
    This code will expire in 10 minutes.
    
    Enter this code on the verification page to continue with your registration.
    
    If you didn't request this code, please ignore this email.
    
    Best regards,
    TrackWise Team
    """
    
    # Send using Infobip
    return send_infobip_email(email, subject, html_content, text_content)