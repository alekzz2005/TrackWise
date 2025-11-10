from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.contrib.auth.models import User
from accounts.models import UserProfile, Company
from .models import StaffProfile
from .forms import StaffUserCreationForm, StaffProfileForm, StaffSearchForm, StaffUpdateForm

@login_required
def staff_list(request):
    """Display staff from the current user's company only"""
    # Get the current user's profile and company
    try:
        current_user_profile = UserProfile.objects.get(user=request.user)
        user_company = current_user_profile.company
    except UserProfile.DoesNotExist:
        messages.error(request, 'Your user profile is not properly configured. Please contact administrator.')
        return redirect('dashboard:dashboard')
    
    # Filter staff profiles by the current user's company
    staff_profiles = StaffProfile.objects.select_related(
        'user_profile', 
        'user_profile__user',
        'user_profile__company'
    ).filter(
        user_profile__company=user_company
    ).order_by('user_profile__user__first_name')
    
    search_form = StaffSearchForm(request.GET)
    
    if search_form.is_valid():
        search_query = search_form.cleaned_data.get('search_query')
        department = search_form.cleaned_data.get('department')
        status = search_form.cleaned_data.get('status')
        
        if search_query:
            staff_profiles = staff_profiles.filter(
                Q(user_profile__user__first_name__icontains=search_query) |
                Q(user_profile__user__last_name__icontains=search_query) |
                Q(user_profile__user__email__icontains=search_query) |
                Q(employee_id__icontains=search_query) |
                Q(position__icontains=search_query) |
                Q(department__icontains=search_query)
            )
        
        if department:
            staff_profiles = staff_profiles.filter(department__icontains=department)
        
        if status:
            staff_profiles = staff_profiles.filter(status=status)
    
    context = {
        'staff_profiles': staff_profiles,
        'search_form': search_form,
        'total_staff': staff_profiles.count(),
        'active_staff': staff_profiles.filter(status='active').count(),
    }
    
    return render(request, 'staff_management/staff_list.html', context)

@login_required
def staff_detail(request, staff_id):
    """Display detailed information about a specific staff member from the same company"""
    # Get the current user's company
    try:
        current_user_profile = UserProfile.objects.get(user=request.user)
        user_company = current_user_profile.company
    except UserProfile.DoesNotExist:
        messages.error(request, 'Your user profile is not properly configured. Please contact administrator.')
        return redirect('staff_management:staff_list')
    
    # Only allow viewing staff from the same company
    staff_profile = get_object_or_404(
        StaffProfile.objects.select_related(
            'user_profile', 
            'user_profile__user',
            'user_profile__company'
        ).filter(
            user_profile__company=user_company
        ), 
        id=staff_id
    )
    
    context = {
        'staff': staff_profile,
    }
    
    return render(request, 'staff_management/staff_detail.html', context)

@login_required
def staff_create(request):
    """Create a new staff account in the current user's company"""
    # Get the current user's company
    try:
        current_user_profile = UserProfile.objects.get(user=request.user)
        company = current_user_profile.company
    except UserProfile.DoesNotExist:
        messages.error(request, 'Your user profile is not properly configured. Please contact administrator.')
        return redirect('staff_management:staff_list')
    
    if request.method == 'POST':
        user_form = StaffUserCreationForm(request.POST)
        profile_form = StaffProfileForm(request.POST)
        
        if user_form.is_valid() and profile_form.is_valid():
            # Create the user
            user = user_form.save(commit=False)
            user.is_active = True
            user.save()
            
            # Create user profile with the current user's company
            user_profile = UserProfile.objects.create(
                user=user,
                role='staff',
                company=company,  # Use the current user's company
                phone_number='',
                assigned_location=profile_form.cleaned_data.get('assigned_locations', '').split(',')[0] if profile_form.cleaned_data.get('assigned_locations') else 'Main Office',
                department=profile_form.cleaned_data.get('department', 'General'),
                position=profile_form.cleaned_data.get('position', ''),
            )
            
            # Create staff profile
            staff_profile = profile_form.save(commit=False)
            staff_profile.user_profile = user_profile
            staff_profile.save()
            
            messages.success(request, f'Staff member {user.get_full_name()} created successfully!')
            return redirect('staff_management:staff_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = StaffUserCreationForm()
        profile_form = StaffProfileForm()
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    
    return render(request, 'staff_management/staff_create.html', context)

@login_required
def staff_update(request, staff_id):
    """Update staff information - only for staff in the same company"""
    # Get the current user's company
    try:
        current_user_profile = UserProfile.objects.get(user=request.user)
        user_company = current_user_profile.company
    except UserProfile.DoesNotExist:
        messages.error(request, 'Your user profile is not properly configured. Please contact administrator.')
        return redirect('staff_management:staff_list')
    
    # Only allow updating staff from the same company
    staff_profile = get_object_or_404(
        StaffProfile.objects.select_related(
            'user_profile', 
            'user_profile__user'
        ).filter(
            user_profile__company=user_company
        ), 
        id=staff_id
    )
    user_profile = staff_profile.user_profile
    user = user_profile.user
    
    if request.method == 'POST':
        profile_form = StaffUpdateForm(request.POST, instance=staff_profile)
        
        if profile_form.is_valid():
            # Update staff profile
            staff_profile = profile_form.save()
            
            # Update user basic info
            user.first_name = profile_form.cleaned_data['first_name']
            user.last_name = profile_form.cleaned_data['last_name']
            user.email = profile_form.cleaned_data['email']
            user.save()
            
            # Update user profile
            user_profile.assigned_location = profile_form.cleaned_data.get('assigned_locations', '').split(',')[0] if profile_form.cleaned_data.get('assigned_locations') else 'Main Office'
            user_profile.department = profile_form.cleaned_data.get('department', 'General')
            user_profile.position = profile_form.cleaned_data.get('position', '')
            user_profile.save()
            
            messages.success(request, f'Staff member {user.get_full_name()} updated successfully!')
            # CHANGED: Redirect to staff_list instead of staff_detail
            return redirect('staff_management:staff_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        profile_form = StaffUpdateForm(instance=staff_profile, initial={
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
        })
    
    context = {
        'staff': staff_profile,
        'profile_form': profile_form,
        'user': user,
    }
    
    return render(request, 'staff_management/staff_update.html', context)

@login_required
def staff_toggle_status(request, staff_id):
    """Toggle staff active/inactive status - only for staff in the same company"""
    if request.method == 'POST':
        # Get the current user's company
        try:
            current_user_profile = UserProfile.objects.get(user=request.user)
            user_company = current_user_profile.company
        except UserProfile.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': 'User profile not configured'
                })
            messages.error(request, 'Your user profile is not properly configured.')
            return redirect('staff_management:staff_list')
        
        # Only allow toggling status for staff from the same company
        staff_profile = get_object_or_404(
            StaffProfile.objects.filter(
                user_profile__company=user_company
            ), 
            id=staff_id
        )
        
        if staff_profile.status == 'active':
            staff_profile.status = 'inactive'
            action = 'deactivated'
        else:
            staff_profile.status = 'active'
            action = 'activated'
        
        staff_profile.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'new_status': staff_profile.status,
                'action': action
            })
        
        messages.success(request, f'Staff member {staff_profile.user_profile.user.get_full_name()} {action} successfully!')
        return redirect('staff_management:staff_list')
    
    return redirect('staff_management:staff_list')