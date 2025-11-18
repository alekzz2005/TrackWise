from django.db import models
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from datetime import timedelta

class Company(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    contact_info = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def staff_count(self):
        """Count staff members in this company"""
        return UserProfile.objects.filter(company=self, role='staff').count()
    
class EmailVerification(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'email_verification'
        ordering = ['-created_at']
        
    def is_expired(self):
        """Check if OTP is expired (10 minutes)"""
        return timezone.now() > self.created_at + timedelta(minutes=10)
    
    def mark_used(self):
        """Mark OTP as used"""
        self.is_used = True
        self.save()
    
    def __str__(self):
        return f"{self.email} - {self.otp}"

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('business_owner', 'Business Owner'),
        ('staff', 'Staff'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    
    # Add the missing fields that exist in your database
    assigned_location = models.CharField(max_length=100, blank=True, default='Main Office')
    department = models.CharField(max_length=100, blank=True, default='General')
    position = models.CharField(max_length=100, blank=True, default='')
    date_joined = models.DateField(auto_now_add=True)  # Matches the date_joined in database
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default='')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.role} - {self.company.name}"
    
    def is_business_owner(self):
        return self.role == 'business_owner'
    
    def is_staff(self):
        return self.role == 'staff'
    
    def get_display_role(self):
        """Get the display name for the role"""
        return dict(self.ROLE_CHOICES).get(self.role, 'User')