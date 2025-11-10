from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class ReportConfiguration(models.Model):
    REPORT_TYPES = [
        ('sales', 'Sales Report'),
        ('staff_activity', 'Staff Activity Report'),
        ('inventory', 'Inventory Report'),
        ('financial', 'Financial Report'),
    ]
    
    EXPORT_FORMATS = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
        ('json', 'JSON'),
    ]
    
    name = models.CharField(max_length=100)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    filters = models.JSONField(default=dict)  # Store report filters
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class GeneratedReport(models.Model):
    report_config = models.ForeignKey(ReportConfiguration, on_delete=models.CASCADE)
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    generated_at = models.DateTimeField(auto_now_add=True)
    file_path = models.CharField(max_length=500, blank=True, null=True)
    file_format = models.CharField(max_length=10, choices=ReportConfiguration.EXPORT_FORMATS)
    parameters = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-generated_at']