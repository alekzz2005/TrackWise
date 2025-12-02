from .models import UserProfile

def user_role_context(request):
    """Add user role and access status information to template context"""
    context = {}
    
    if request.user.is_authenticated:
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            context['user_profile'] = user_profile
            context['is_business_owner'] = user_profile.is_business_owner()
            context['is_staff'] = user_profile.is_staff()
            context['user_display_role'] = user_profile.get_display_role()
            
            # Add access status check
            context['can_access'] = user_profile.should_allow_access()
            
            # Add status information for display
            try:
                from staff_management.models import StaffProfile
                staff_profile = StaffProfile.objects.get(user_profile=user_profile)
                context['staff_status'] = staff_profile.status
                context['is_active_staff'] = staff_profile.status == 'active'
            except ImportError:
                # staff_management app might not be available
                context['staff_status'] = 'active' if user_profile.is_active else 'inactive'
                context['is_active_staff'] = user_profile.is_active
            except StaffProfile.DoesNotExist:
                # No staff profile exists (could be business owner or staff without detailed profile)
                context['staff_status'] = 'active' if user_profile.is_active else 'inactive'
                context['is_active_staff'] = user_profile.is_active
                
        except UserProfile.DoesNotExist:
            # Fallback for users without profile
            context['is_business_owner'] = request.user.is_superuser
            context['is_staff'] = request.user.is_staff
            context['user_display_role'] = 'Administrator' if request.user.is_superuser else 'User'
            context['can_access'] = True  # Superusers always have access
            context['is_active_staff'] = True
            context['staff_status'] = 'active'
    
    return context