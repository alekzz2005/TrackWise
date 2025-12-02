from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import logout
from django.urls import reverse

class UserStatusMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip for non-authenticated users
        if request.user.is_authenticated:
            try:
                # Get user profile
                profile = request.user.userprofile
                
                # Check if user should be allowed access
                if not profile.should_allow_access():
                    # Force logout and redirect to login page
                    logout(request)
                    messages.warning(request, 'Your account has been deactivated or placed on leave. Please contact your administrator.')
                    
                    # Redirect to login page, excluding logout endpoint itself
                    if request.path != reverse('accounts:logout'):
                        return redirect('accounts:login')
            except AttributeError:
                # User has no profile, allow admin to handle
                pass
            except Exception as e:
                # Log error but don't break the site
                print(f"Error in UserStatusMiddleware: {e}")

        response = self.get_response(request)
        return response