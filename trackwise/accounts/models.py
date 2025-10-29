from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Company(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    contact_info = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('business_owner', 'Business Owner'),
        ('staff', 'Staff'),
    ]
    
    # MOVE DEPARTMENT_CHOICES HERE - before it's used
    DEPARTMENT_CHOICES = [
        ('sales', 'Sales'),
        ('inventory', 'Inventory Management'),
        ('customer_service', 'Customer Service'),
        ('administration', 'Administration'),
        ('other', 'Other'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    
    # Staff assignment fields
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, default='other')
    position = models.CharField(max_length=100, blank=True)
    date_joined = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    assigned_location = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.role} - {self.company.name}"