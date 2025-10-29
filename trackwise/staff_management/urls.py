from django.urls import path
from . import views

app_name = 'staff_management'

urlpatterns = [
    path('', views.staff_list, name='staff_list'),
    path('<int:staff_id>/', views.staff_detail, name='staff_detail'),
]