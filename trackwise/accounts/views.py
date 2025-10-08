from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import time
from .forms import BusinessOwnerRegistrationForm, StaffRegistrationForm, CustomAuthenticationForm
from .models import UserProfile, Company  # Import both models here
from inventory.models import Product

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
        company = Company.objects.first()
        if not company:
            company = Company.objects.create(name="Default Company")
        profile = UserProfile.objects.create(user=request.user, role='staff', company=company)
    
    # Calculate dashboard statistics
    if profile.role == 'business_owner':
        # Get products for this company
        products = Product.objects.filter(company=profile.company)
        
        # Calculate statistics
        total_products = products.count()
        low_stock = products.filter(quantity__gt=0, quantity__lte=10).count()  # 10 or less is low stock
        out_of_stock = products.filter(quantity=0).count()
        
        # Get total staff count (users in the same company with staff role)
        total_staff = UserProfile.objects.filter(company=profile.company, role='staff').count()
        
        # Get recent products (last 5 added)
        recent_products = products.order_by('-created_at')[:5]
        
        # Calculate total inventory value
        total_inventory_value = sum(product.total_value for product in products)
        
        # Get recently updated products for activity feed
        recent_activity = products.order_by('-updated_at')[:10]
        
        context = {
            'profile': profile,
            'total_products': total_products,
            'low_stock': low_stock,
            'out_of_stock': out_of_stock,
            'total_staff': total_staff,
            'recent_products': recent_products,
            'recent_activity': recent_activity,
            'total_inventory_value': total_inventory_value,
        }
        template = 'accounts/business_owner_dashboard.html'
    else:
        # Staff dashboard - calculate similar statistics but for staff view
        products = Product.objects.filter(company=profile.company)
        
        # Calculate statistics for staff
        total_products = products.count()
        low_stock = products.filter(quantity__gt=0, quantity__lte=10).count()
        out_of_stock = products.filter(quantity=0).count()
        
        # Get recent products (last 5 added)
        recent_products = products.order_by('-created_at')[:5]
        
        # Get recently updated products for activity feed
        recent_activity = products.order_by('-updated_at')[:10]
        
        # Count today's updates (products updated today)
        from django.utils import timezone
        from datetime import timedelta
        today = timezone.now().date()
        recent_updates = products.filter(updated_at__date=today).count()
        
        context = {
            'profile': profile,
            'total_products': total_products,
            'low_stock': low_stock,
            'out_of_stock': out_of_stock,
            'recent_updates': recent_updates,
            'recent_products': recent_products,
            'recent_activity': recent_activity,
        }
        template = 'accounts/staff_dashboard.html'
    
    return render(request, template, context)