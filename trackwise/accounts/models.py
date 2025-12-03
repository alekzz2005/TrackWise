from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import base64

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

# REMOVE or COMMENT OUT this entire model since we're not using OTP anymore
# class EmailVerification(models.Model):
#     email = models.EmailField()
#     otp = models.CharField(max_length=6)
#     created_at = models.DateTimeField(auto_now_add=True)
#     is_used = models.BooleanField(default=False)
#     
#     class Meta:
#         db_table = 'email_verification'
#         ordering = ['-created_at']
#         
#     def is_expired(self):
#         """Check if OTP is expired (10 minutes)"""
#         return timezone.now() > self.created_at + timedelta(minutes=10)
#     
#     def mark_used(self):
#         """Mark OTP as used"""
#         self.is_used = True
#         self.save()
#     
#     def __str__(self):
#         return f"{self.email} - {self.otp}"

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('business_owner', 'Business Owner'),
        ('staff', 'Staff'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, blank=True)
    
    # Change from ImageField to TextField for BLOB/base64 storage
    profile_picture = models.TextField(blank=True, null=True, help_text="Base64 encoded profile picture")
    profile_picture_content_type = models.CharField(max_length=50, blank=True, null=True, help_text="MIME type of the profile picture")
    
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
    
    @property
    def profile_picture_base64(self):
        """Get profile picture as base64 data URL for HTML display."""
        if self.profile_picture:
            try:
                # Remove any existing data URL prefix if present
                image_data = self.profile_picture
                if image_data.startswith('data:'):
                    # Extract just the base64 part
                    parts = image_data.split(',', 1)
                    if len(parts) > 1:
                        image_data = parts[1]
                
                return f"data:{self.profile_picture_content_type or 'image/jpeg'};base64,{image_data}"
            except Exception as e:
                print(f"Error in profile_picture_base64: {e}")
                return None
        return None
    
    def set_profile_picture_from_file(self, uploaded_file):
        """Set profile picture from uploaded file."""
        if uploaded_file:
            try:
                # Read file content
                file_content = uploaded_file.read()
                
                # Encode to base64
                encoded = base64.b64encode(file_content).decode('utf-8')
                
                # Store in profile_picture field
                self.profile_picture = encoded
                self.profile_picture_content_type = uploaded_file.content_type
                return True
            except Exception as e:
                print(f"Error setting profile picture: {e}")
                return False
        return False
    
    def should_allow_access(self):
        """
        Check if user should be allowed to access the system.
        Staff members are blocked if their profile is inactive or if their StaffProfile status is inactive/on_leave.
        """
        # Always allow business owners
        if self.role == 'business_owner':
            return True
            
        # Check UserProfile's is_active field
        if not self.is_active:
            return False
            
        # Check if there's a StaffProfile with inactive or on_leave status
        try:
            from staff_management.models import StaffProfile
            staff_profile = StaffProfile.objects.get(user_profile=self)
            if staff_profile.status in ['inactive', 'on_leave']:
                return False
        except StaffProfile.DoesNotExist:
            # If no StaffProfile exists, allow access based on UserProfile.is_active
            pass
            
        return True