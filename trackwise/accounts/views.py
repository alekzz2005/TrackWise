from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import BusinessOwnerRegistrationForm, StaffRegistrationForm, CustomAuthenticationForm, BusinessOwnerProfileForm, CustomPasswordChangeForm, CompanyForm
from .models import UserProfile, Company
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
from .models import EmailVerification
from django.core.mail import send_mail
from django.http import HttpResponse

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

def business_owner_register(request):
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
        
    if request.method == 'POST':
        form = BusinessOwnerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
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
    else:
        form = BusinessOwnerRegistrationForm()
    
    return render(request, 'accounts/business_owner_register.html', {'form': form})

def staff_register(request):
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
        
    if request.method == 'POST':
        form = StaffRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Always show processing screen for staff
            return render(request, 'accounts/processing.html', {
                'role': 'staff',
                'next_url': 'accounts:login'
            })
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StaffRegistrationForm()
    
    return render(request, 'accounts/staff_register.html', {'form': form})

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
        
        # Send email
        try:
            send_mail(
                'Your TrackWise Verification Code',
                f'Your verification code is: {otp}\n\nThis code will expire in 10 minutes.\n\nIf you didn\'t request this code, please ignore this email.',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            print(f"OTP sent via email to {email}: {otp}")
        except Exception as e:
            print(f"Email sending failed: {e}")
            print(f"DEVELOPMENT OTP for {email}: {otp}")
            
            # In production, we should still return success for now to avoid blocking users
            # You might want to implement a proper email service later
            if not settings.DEBUG:
                # Log the error but don't block the user in production
                pass
        
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
        
        # Clean up used OTPs
        EmailVerification.objects.filter(
            email=email,
            is_used=True
        ).delete()
        
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
                return redirect('accounts:edit_profile')
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