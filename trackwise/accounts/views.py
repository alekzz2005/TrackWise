from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .forms import BusinessOwnerRegistrationForm, StaffRegistrationForm, CustomAuthenticationForm, BusinessOwnerProfileForm, CustomPasswordChangeForm, CompanyForm
from .models import UserProfile, Company, EmailVerification
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import random
import string
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import secrets
from django.core.mail import send_mail
from django.http import HttpResponse

# ADD THIS NEW VIEW
def email_verification_view(request):
    """Display email verification page"""
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    
    email = request.GET.get('email', '')
    if not email:
        return redirect('accounts:role_selection')
    
    return render(request, 'accounts/email_verification.html', {
        'email': email
    })

def test_email_config(request):
    """Test email configuration"""
    try:
        send_mail(
            'TrackWise Email Test',
            'This is a test email from TrackWise. If you receive this, your email configuration is working!',
            settings.DEFAULT_FROM_EMAIL,
            [settings.EMAIL_HOST_USER],  # Send to yourself
            fail_silently=False,
        )
        return HttpResponse("✅ Test email sent successfully! Please check your inbox.")
    except Exception as e:
        return HttpResponse(f"❌ Failed to send test email: {str(e)}")

def role_selection(request):
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    return render(request, 'accounts/role_selection.html')

def landing_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    return render(request, 'landing.html')

# UPDATED BUSINESS OWNER REGISTRATION
def business_owner_register(request):
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    
    if request.method == 'GET':
        email = request.GET.get('email', '')
        if email:
            # Check if email is verified before showing form
            is_verified = EmailVerification.objects.filter(
                email=email.lower(),
                is_used=True
            ).exists()
            
            if not is_verified:
                # Not verified, show error and redirect to verification
                messages.error(request, 'Please verify your email before registering.')
                return redirect(f'{reverse("accounts:email_verification")}?email={email}')
            
            # Email is verified, show pre-filled form
            form = BusinessOwnerRegistrationForm(initial={'email': email})
        else:
            form = BusinessOwnerRegistrationForm()
        
        return render(request, 'accounts/business_owner_register.html', {'form': form})
    
    # POST request - processing registration form
    form = BusinessOwnerRegistrationForm(request.POST)
    if form.is_valid():
        email = form.cleaned_data.get('email', '').lower()
        
        # CHECK IF EMAIL IS VERIFIED
        is_verified = EmailVerification.objects.filter(
            email=email,
            is_used=True
        ).exists()
        
        if not is_verified:
            messages.error(request, 'Please verify your email before registering.')
            return redirect(f'{reverse("accounts:email_verification")}?email={email}')
        
        # Email is verified, create user
        user = form.save()
        
        # Delete the verification record after successful registration
        EmailVerification.objects.filter(email=email, is_used=True).delete()
        
        # Show processing screen for existing company selection
        if form.cleaned_data.get('company_choice') == 'existing':
            return render(request, 'accounts/processing.html', {
                'role': 'business_owner',
                'next_url': 'accounts:login'
            })
        
        login(request, user)
        messages.success(request, 'Business Owner account created successfully! Welcome to TrackWise.')
        return redirect('dashboard:dashboard')
    else:
        messages.error(request, 'Please correct the errors below.')
    
    return render(request, 'accounts/business_owner_register.html', {'form': form})

# UPDATED STAFF REGISTRATION
def staff_register(request):
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    
    if request.method == 'GET':
        email = request.GET.get('email', '')
        if email:
            # Check if email is verified before showing form
            is_verified = EmailVerification.objects.filter(
                email=email.lower(),
                is_used=True
            ).exists()
            
            if not is_verified:
                # Not verified, show error and redirect to verification
                messages.error(request, 'Please verify your email before registering.')
                return redirect(f'{reverse("accounts:email_verification")}?email={email}')
            
            # Email is verified, show pre-filled form
            form = StaffRegistrationForm(initial={'email': email})
        else:
            form = StaffRegistrationForm()
        
        return render(request, 'accounts/staff_register.html', {'form': form})
    
    # POST request - processing registration form
    form = StaffRegistrationForm(request.POST)
    if form.is_valid():
        email = form.cleaned_data.get('email', '').lower()
        
        # CHECK IF EMAIL IS VERIFIED
        is_verified = EmailVerification.objects.filter(
            email=email,
            is_used=True
        ).exists()
        
        if not is_verified:
            messages.error(request, 'Please verify your email before registering.')
            return redirect(f'{reverse("accounts:email_verification")}?email={email}')
        
        # Email is verified, create user
        user = form.save()
        
        # Delete the verification record after successful registration
        EmailVerification.objects.filter(email=email, is_used=True).delete()
        
        # Always show processing screen for staff
        return render(request, 'accounts/processing.html', {
            'role': 'staff',
            'next_url': 'accounts:login'
        })
    else:
        messages.error(request, 'Please correct the errors below.')
    
    return render(request, 'accounts/staff_register.html', {'form': form})

# ADD THIS HELPER FUNCTION FOR REDIRECTING TO VERIFICATION
def check_and_redirect_verification(email):
    """Check if email is verified, if not redirect to verification page"""
    is_verified = EmailVerification.objects.filter(
        email=email.lower(),
        is_used=True
    ).exists()
    
    if not is_verified:
        return redirect(f'{reverse("accounts:email_verification")}?email={email}')
    return None

@require_POST
@csrf_exempt
def send_verification_code(request):
    """Send OTP code to email for verification"""
    try:
        # Check if it's JSON data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            email = data.get('email', '').strip().lower()
        else:
            # Fallback to form data
            email = request.POST.get('email', '').strip().lower()
        
        # Validate email format
        if not email or '@' not in email:
            return JsonResponse({'success': False, 'error': 'Invalid email address'})
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'error': 'This email is already registered'})
        
        # Generate secure random OTP (6 digits)
        otp = ''.join(secrets.choice(string.digits) for _ in range(6))
        
        # Delete any existing OTPs for this email
        EmailVerification.objects.filter(email=email).delete()
        
        # Create new OTP record
        verification = EmailVerification.objects.create(
            email=email,
            otp=otp
        )
        
        # Send email with HTML formatting
        try:
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
                    
                    <div class="otp-code">{otp}</div>
                    
                    <div class="note">
                        <strong>Important:</strong> This code will expire in 10 minutes. Please do not share this code with anyone.
                    </div>
                    
                    <p>If you didn't request this verification code, please ignore this email or contact our support team if you have concerns.</p>
                    
                    <p>Best regards,<br>
                    <strong>The TrackWise Team</strong></p>
                </div>
                
                <div class="footer">
                    <p>This email was sent to {email} as part of your TrackWise registration.</p>
                    <p>© {timezone.now().year} TrackWise. All rights reserved.</p>
                </div>
            </body>
            </html>
            """
            
            # Plain text content
            text_content = f"""
            Welcome to TrackWise!
            
            Your verification code is: {otp}
            
            This code will expire in 10 minutes.
            
            Enter this code on the verification page to continue with your registration.
            
            If you didn't request this code, please ignore this email.
            
            Best regards,
            TrackWise Team
            """
            
            # Send email using EmailMultiAlternatives for HTML support
            from django.core.mail import EmailMultiAlternatives
            
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email],
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)
            
            print(f"✅ Email sent successfully to {email}")
            
        except Exception as e:
            print(f"❌ Email sending failed: {e}")
            if settings.DEBUG:
                print(f"DEBUG OTP for {email}: {otp}")
        
        return JsonResponse({'success': True})
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        print(f"Error in send_verification_code: {str(e)}")
        return JsonResponse({'success': False, 'error': 'An error occurred. Please try again.'})

@require_POST
@csrf_exempt
def verify_email_code(request):
    """Verify the OTP code entered by user"""
    try:
        # Check if it's JSON data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
            
        email = data.get('email', '').strip().lower()
        code = data.get('code', '').strip()
        
        if not email or not code:
            return JsonResponse({'success': False, 'error': 'Email and code are required'})
        
        # Find the most recent valid OTP for this email
        try:
            verification = EmailVerification.objects.filter(
                email=email,
                is_used=False
            ).latest('created_at')
        except EmailVerification.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Verification code not found or expired. Please request a new code.'})
        
        # Check if OTP is expired
        if verification.is_expired():
            verification.delete()
            return JsonResponse({'success': False, 'error': 'Verification code has expired. Please request a new code.'})
        
        # Verify the code
        if verification.otp != code:
            return JsonResponse({'success': False, 'error': 'Invalid verification code'})
        
        # Mark OTP as used
        verification.mark_used()
        
        # Clean up old OTPs (keep only the used one)
        EmailVerification.objects.filter(
            email=email,
            is_used=False
        ).exclude(id=verification.id).delete()
        
        return JsonResponse({'success': True})
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        print(f"Error in verify_email_code: {str(e)}")
        return JsonResponse({'success': False, 'error': 'An error occurred during verification'})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
        
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                next_url = request.GET.get('next', 'dashboard:dashboard')
                return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('accounts:login')

@require_POST
@csrf_exempt
def check_email(request):
    data = json.loads(request.body)
    email = data.get('email', '')
    
    exists = User.objects.filter(email=email).exists()
    return JsonResponse({'is_available': not exists})

@require_POST
@csrf_exempt
def check_username(request):
    data = json.loads(request.body)
    username = data.get('username', '')
    
    exists = User.objects.filter(username=username).exists()
    return JsonResponse({'is_available': not exists})

@login_required
def edit_profile(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        messages.error(request, 'Profile not found.')
        return redirect('dashboard:dashboard')
    
    company = profile.company
    
    if request.method == 'POST':
        # Determine which form was submitted
        form_type = request.POST.get('form_type')
        
        if form_type == 'profile':
            # Only validate and save profile form
            profile_form = BusinessOwnerProfileForm(
                request.POST, 
                request.FILES, 
                instance=profile,
                user=request.user
            )
            company_form = CompanyForm(instance=company)  # Keep existing company data
            
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('accounts:edit_profile')
            else:
                messages.error(request, 'Please correct the errors in your profile information.')
                
        elif form_type == 'company':
            # Only validate and save company form
            profile_form = BusinessOwnerProfileForm(instance=profile, user=request.user)  # Keep existing profile data
            company_form = CompanyForm(request.POST, instance=company)
            
            if company_form.is_valid():
                company_form.save()
                messages.success(request, 'Company information updated successfully!')
                return redirect('accounts:email_verification')
            else:
                messages.error(request, 'Please correct the errors in your company information.')
        else:
            # Fallback - handle both forms (original behavior)
            profile_form = BusinessOwnerProfileForm(
                request.POST, 
                request.FILES, 
                instance=profile,
                user=request.user
            )
            company_form = CompanyForm(request.POST, instance=company)
            
            if profile_form.is_valid() and company_form.is_valid():
                profile_form.save()
                company_form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('accounts:edit_profile')
            else:
                messages.error(request, 'Please correct the errors below.')
    else:
        # GET request - initialize both forms
        profile_form = BusinessOwnerProfileForm(instance=profile, user=request.user)
        company_form = CompanyForm(instance=company)
    
    context = {
        'profile_form': profile_form,
        'company_form': company_form,
        'profile': profile,
    }
    return render(request, 'accounts/edit_profile.html', context)

@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('accounts:edit_profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomPasswordChangeForm(request.user)
    
    return render(request, 'accounts/change_password.html', {'form': form})