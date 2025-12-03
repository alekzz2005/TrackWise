from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('role-selection/', views.role_selection, name='role_selection'),
    # REMOVE THIS LINE: path('email-verification/', views.email_verification_view, name='email_verification'),
    path('register/business-owner/', views.business_owner_register, name='business_owner_register'),
    path('register/staff/', views.staff_register, name='staff_register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),

    # API endpoints - You can uncomment these if you're using them
    path('api/check-email/', views.check_email, name='check_email'),
    path('api/check-username/', views.check_username, name='check_username'),
    
    # Test email - You can uncomment these if you're using them
    # path('test-email/', views.test_email_config, name='test_email'),
    # path('debug-email/', views.debug_email_config, name='debug_email'),
]