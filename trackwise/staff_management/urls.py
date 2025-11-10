from django.urls import path
from . import views

app_name = 'staff_management'

urlpatterns = [
    path('', views.staff_list, name='staff_list'),
    path('create/', views.staff_create, name='staff_create'),
    path('<int:staff_id>/', views.staff_detail, name='staff_detail'),
    path('<int:staff_id>/update/', views.staff_update, name='staff_update'),
    path('<int:staff_id>/toggle-status/', views.staff_toggle_status, name='staff_toggle_status'),
]