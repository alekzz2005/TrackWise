from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('role-selection/', views.role_selection, name='role_selection'),
    path('email-verification/', views.email_verification_view, name='email_verification'),  # ADD THIS
    path('register/business-owner/', views.business_owner_register, name='business_owner_register'),
    path('register/staff/', views.staff_register, name='staff_register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),

    # API endpoints
    path('api/check-email/', views.check_email, name='check_email'),
    path('api/check-username/', views.check_username, name='check_username'),
    path('api/send-verification-code/', views.send_verification_code, name='send_verification_code'),
    path('api/verify-email-code/', views.verify_email_code, name='verify_email_code'),
    
    # Test email
    path('test-email/', views.test_email_config, name='test_email'),
]