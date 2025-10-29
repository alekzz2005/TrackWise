from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_dashboard, name='reports_dashboard'),
    path('staff-activity/', views.staff_activity_report, name='staff_activity_report'),
    path('inventory/', views.inventory_report, name='inventory_report'),
]