from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.landing_page, name='landing'),  # Landing page as root
    path('role-selection/', views.role_selection, name='role_selection'),
    path('register/business-owner/', views.business_owner_register, name='business_owner_register'),
    path('register/staff/', views.staff_register, name='staff_register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),

    path('api/check-email/', views.check_email, name='check_email'),
    path('api/check-username/', views.check_username, name='check_username'),
]