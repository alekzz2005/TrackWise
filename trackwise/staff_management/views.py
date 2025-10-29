from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from accounts.models import UserProfile, Company
from django.core.paginator import Paginator

@login_required
def staff_list(request):
    """View all staff members with filtering and search"""
    # Check if user is business owner
    try:
        if request.user.userprofile.role != 'business_owner':
            messages.error(request, 'You do not have permission to view this page.')
            return redirect('dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('dashboard')
    
    company = request.user.userprofile.company
    staff_members = UserProfile.objects.filter(company=company, role='staff').order_by('user__first_name')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        staff_members = staff_members.filter(
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(department__icontains=search_query) |
            Q(position__icontains=search_query)
        )
    
    # Filter by department
    department_filter = request.GET.get('department', '')
    if department_filter:
        staff_members = staff_members.filter(department=department_filter)
    
    # Filter by active status
    active_filter = request.GET.get('active', '')
    if active_filter == 'active':
        staff_members = staff_members.filter(is_active=True)
    elif active_filter == 'inactive':
        staff_members = staff_members.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(staff_members, 10)  # Show 10 staff per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'staff_members': page_obj,
        'search_query': search_query,
        'department_filter': department_filter,
        'active_filter': active_filter,
        'departments': UserProfile.DEPARTMENT_CHOICES,
    }
    return render(request, 'staff_management/staff_list.html', context)

@login_required
def staff_detail(request, staff_id):
    """Show detailed information about a staff member"""
    try:
        if request.user.userprofile.role != 'business_owner':
            messages.error(request, 'You do not have permission to view this page.')
            return redirect('dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('dashboard')
    
    staff_profile = get_object_or_404(
        UserProfile, 
        id=staff_id, 
        role='staff', 
        company=request.user.userprofile.company
    )
    
    context = {
        'staff': staff_profile,
    }
    return render(request, 'staff_management/staff_detail.html', context)