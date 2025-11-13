from django.db import models
from django.contrib.auth.models import User
from accounts.models import UserProfile, Company

class IssueReport(models.Model):
    ISSUE_TYPE_CHOICES = [
        ('system_error', 'System Error'),
        ('stock_discrepancy', 'Stock Discrepancy'),
        ('missing_item', 'Missing Item'),
        ('damaged_goods', 'Damaged Goods'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    # Basic issue information
    title = models.CharField(max_length=200)
    description = models.TextField()
    issue_type = models.CharField(max_length=50, choices=ISSUE_TYPE_CHOICES)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Relationships
    reporter = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='reported_issues')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='issues')
    
    # File attachments
    attachment = models.FileField(upload_to='issue_attachments/', blank=True, null=True)
    image = models.ImageField(upload_to='issue_images/', blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"

class IssueComment(models.Model):
    issue = models.ForeignKey(IssueReport, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_business_owner_note = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.author.user.username} on {self.issue.title}"