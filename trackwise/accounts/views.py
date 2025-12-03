from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .forms import BusinessOwnerRegistrationForm, StaffRegistrationForm, CustomAuthenticationForm, BusinessOwnerProfileForm, CustomPasswordChangeForm, CompanyForm
from .models import UserProfile, Company
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json

# REMOVE: Remove EmailVerification import
# REMOVE: from .models import UserProfile, Company, EmailVerification

# REMOVE: Remove email_verification_view function
# REMOVE: def email_verification_view(request):
# REMOVE:     """Display email verification page"""
# REMOVE:     if request.user.is_authenticated:
# REMOVE:         return redirect('dashboard:dashboard')
# REMOVE:    
# REMOVE:     email = request.GET.get('email', '')
# REMOVE:     if not email:
# REMOVE:         return redirect('accounts:role_selection')
# REMOVE:    
# REMOVE:     return render(request, 'accounts/email_verification.html', {
# REMOVE:         'email': email
# REMOVE:     })

def role_selection(request):
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    return render(request, 'accounts/role_selection.html')

def landing_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    return render(request, 'landing.html')

# UPDATED BUSINESS OWNER REGISTRATION (Simplified - No OTP, No Company Choice)
def business_owner_register(request):
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        form = BusinessOwnerRegistrationForm(request.POST)
        if form.is_valid():
            # Create user directly (no OTP verification)
            user = form.save()
            
            # REMOVE: Company choice logic since we're always creating new company
            # if form.cleaned_data.get('company_choice') == 'existing':
            #     return render(request, 'accounts/processing.html', {
            #         'role': 'business_owner',
            #         'next_url': 'accounts:login'
            #     })
            
            # Login the user immediately
            login(request, user)
            messages.success(request, 'Business Owner account created successfully! Welcome to TrackWise.')
            return redirect('dashboard:dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BusinessOwnerRegistrationForm()
    
    return render(request, 'accounts/business_owner_register.html', {'form': form})

# UPDATED STAFF REGISTRATION (Simplified - No OTP)
def staff_register(request):
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        form = StaffRegistrationForm(request.POST)
        if form.is_valid():
            # Create user directly (no OTP verification)
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

# REMOVE: Remove OTP-related functions
# REMOVE: @require_POST
# REMOVE: @csrf_exempt
# REMOVE: def send_verification_code(request):
# REMOVE:     ...

# REMOVE: @require_POST
# REMOVE: @csrf_exempt
# REMOVE: def verify_email_code(request):
# REMOVE:     ...

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
                # Check if user should be allowed to login
                try:
                    profile = user.userprofile
                    if not profile.should_allow_access():
                        messages.error(request, 'Your account is currently inactive or on leave. Please contact your administrator.')
                        return render(request, 'accounts/login.html', {'form': form})
                except UserProfile.DoesNotExist:
                    # No profile found - could redirect to setup or show error
                    messages.error(request, 'User profile not found. Please contact administrator.')
                    return render(request, 'accounts/login.html', {'form': form})
                
                # User is allowed, proceed with login
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