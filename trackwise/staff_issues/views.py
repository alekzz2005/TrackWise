from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from accounts.models import UserProfile
from .models import IssueReport, IssueComment
from .forms import IssueReportForm, IssueCommentForm

@login_required
def report_issue(request):
    """Staff can submit new issue reports"""
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        form = IssueReportForm(request.POST, request.FILES)
        if form.is_valid():
            issue = form.save(commit=False)
            issue.reporter = profile
            issue.company = profile.company
            issue.save()
            
            messages.success(request, 'Issue reported successfully! We will look into it soon.')
            return redirect('staff_issues:issue_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = IssueReportForm()
    
    context = {
        'form': form,
        'profile': profile,
    }
    return render(request, 'staff_issues/report_issue.html', context)

@login_required
def issue_list(request):
    """View all issues for the current user's company"""
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('dashboard:dashboard')
    
    # Staff can only see issues from their company
    issues = IssueReport.objects.filter(company=profile.company).select_related(
        'reporter', 'reporter__user'
    ).prefetch_related('comments').order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        issues = issues.filter(status=status_filter)
    
    # Filter by issue type if provided
    type_filter = request.GET.get('type')
    if type_filter:
        issues = issues.filter(issue_type=type_filter)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        issues = issues.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Count issues by status for statistics
    status_counts = {
        'pending': issues.filter(status='pending').count(),
        'in_progress': issues.filter(status='in_progress').count(),
        'resolved': issues.filter(status='resolved').count(),
        'closed': issues.filter(status='closed').count(),
        'total': issues.count(),
    }
    
    context = {
        'issues': issues,
        'profile': profile,
        'current_status': status_filter,
        'current_type': type_filter,
        'search_query': search_query,
        'status_counts': status_counts,
    }
    return render(request, 'staff_issues/issue_list.html', context)

@login_required
def issue_detail(request, issue_id):
    """View issue details and add comments"""
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('dashboard:dashboard')
    
    # Staff can only see issues from their company
    issue = get_object_or_404(
        IssueReport.objects.select_related('reporter', 'reporter__user', 'company'),
        id=issue_id,
        company=profile.company
    )
    
    comments = issue.comments.select_related('author', 'author__user').all()
    
    if request.method == 'POST':
        # Handle comment submission
        comment_form = IssueCommentForm(request.POST, user_profile=profile)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.issue = issue
            comment.author = profile
            comment.save()
            
            messages.success(request, 'Comment added successfully!')
            return redirect('staff_issues:issue_detail', issue_id=issue.id)
        else:
            messages.error(request, 'Please correct the errors in your comment.')
    
    else:
        comment_form = IssueCommentForm(user_profile=profile)
    
    context = {
        'issue': issue,
        'comments': comments,
        'comment_form': comment_form,
        'profile': profile,
        'can_update_status': profile.role == 'business_owner',  # Only business owners can update status
    }
    return render(request, 'staff_issues/issue_detail.html', context)

@login_required
def update_issue_status(request, issue_id):
    """Business owners can update issue status"""
    if request.method == 'POST':
        try:
            profile = request.user.userprofile
        except UserProfile.DoesNotExist:
            messages.error(request, 'User profile not found.')
            return redirect('dashboard:dashboard')
        
        # Only business owners can update status
        if profile.role != 'business_owner':
            messages.error(request, 'You do not have permission to update issue status.')
            return redirect('staff_issues:issue_list')
        
        issue = get_object_or_404(
            IssueReport.objects.filter(company=profile.company),
            id=issue_id
        )
        
        new_status = request.POST.get('status')
        if new_status in dict(IssueReport.STATUS_CHOICES):
            issue.status = new_status
            if new_status in ['resolved', 'closed']:
                issue.resolved_at = timezone.now()
            issue.save()
            messages.success(request, f'Issue status updated to {issue.get_status_display()}')
        else:
            messages.error(request, 'Invalid status selected.')
    
    return redirect('staff_issues:issue_detail', issue_id=issue_id)

@login_required
def my_reported_issues(request):
    """View issues reported by the current user"""
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        messages.error(request, 'User profile not found.')
        return redirect('dashboard:dashboard')
    
    issues = IssueReport.objects.filter(
        reporter=profile,
        company=profile.company
    ).select_related('reporter', 'reporter__user').order_by('-created_at')
    
    context = {
        'issues': issues,
        'profile': profile,
        'is_my_issues': True,
    }
    return render(request, 'staff_issues/issue_list.html', context)