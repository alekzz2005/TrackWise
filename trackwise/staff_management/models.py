from django.db import models
from django.contrib.auth.models import User
from accounts.models import UserProfile, Company

class StaffProfile(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('on_leave', 'On Leave'),
    ]
    
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=50, unique=True)
    position = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    hire_date = models.DateField()
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    assigned_locations = models.TextField(help_text="Comma-separated list of assigned locations")
    permissions = models.JSONField(default=dict, blank=True, help_text="JSON object storing staff permissions")  # Add blank=True
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user_profile.user.get_full_name()} - {self.position}"
    
    class Meta:
        db_table = 'staff_management_staffprofile'
        verbose_name = 'Staff Profile'
        verbose_name_plural = 'Staff Profiles'