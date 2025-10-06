from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import time
from .forms import BusinessOwnerRegistrationForm, StaffRegistrationForm, CustomAuthenticationForm
from .models import UserProfile

def role_selection(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'accounts/role_selection.html')

def business_owner_register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = BusinessOwnerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Show processing screen for existing company selection
            if form.cleaned_data.get('company_choice') == 'existing':
                return render(request, 'accounts/processing.html', {
                    'role': 'business_owner',
                    'next_url': 'login'
                })
            
            login(request, user)
            messages.success(request, 'Business Owner account created successfully! Welcome to TrackWise.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BusinessOwnerRegistrationForm()
    
    return render(request, 'accounts/business_owner_register.html', {'form': form})

def staff_register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = StaffRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Always show processing screen for staff
            return render(request, 'accounts/processing.html', {
                'role': 'staff',
                'next_url': 'login'
            })
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StaffRegistrationForm()
    
    return render(request, 'accounts/staff_register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')

@login_required
def dashboard_view(request):
    # Ensure user has a profile
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        # Create a default profile if it doesn't exist
        from .models import UserProfile, Company
        company = Company.objects.first()
        if not company:
            company = Company.objects.create(name="Default Company")
        profile = UserProfile.objects.create(user=request.user, role='staff', company=company)
    
    # Render different dashboards based on role
    if profile.role == 'business_owner':
        template = 'accounts/business_owner_dashboard.html'
    else:
        template = 'accounts/staff_dashboard.html'
    
    return render(request, template, {'profile': profile})