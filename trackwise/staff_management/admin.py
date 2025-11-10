from django.contrib import admin
from .models import StaffProfile

@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'get_full_name', 'position', 'department', 'status', 'hire_date')
    list_filter = ('status', 'department', 'hire_date')
    search_fields = ('employee_id', 'user_profile__user__first_name', 'user_profile__user__last_name', 'user_profile__user__email')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_full_name(self, obj):
        return obj.user_profile.user.get_full_name()
    get_full_name.short_description = 'Full Name'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user_profile', 'employee_id', 'position', 'department', 'hire_date')
        }),
        ('Employment Details', {
            'fields': ('salary', 'status', 'assigned_locations')
        }),
        ('Additional Information', {
            'fields': ('permissions', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )