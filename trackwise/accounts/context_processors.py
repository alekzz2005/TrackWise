from .models import UserProfile

def user_role_context(request):
    """Add user role information to template context"""
    context = {}
    
    if request.user.is_authenticated:
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            context['user_profile'] = user_profile
            context['is_business_owner'] = user_profile.is_business_owner()
            context['is_staff'] = user_profile.is_staff()
            context['user_display_role'] = user_profile.get_display_role()
            
        except UserProfile.DoesNotExist:
            # Fallback for users without profile
            context['is_business_owner'] = request.user.is_superuser
            context['is_staff'] = request.user.is_staff
            context['user_display_role'] = 'Administrator' if request.user.is_superuser else 'User'
    
    return context