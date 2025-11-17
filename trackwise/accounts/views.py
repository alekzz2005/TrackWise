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