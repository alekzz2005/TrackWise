from django.contrib import admin
from .models import IssueReport, IssueComment

@admin.register(IssueReport)
class IssueReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'issue_type', 'status', 'priority', 'reporter', 'company', 'created_at']
    list_filter = ['status', 'issue_type', 'priority', 'company', 'created_at']
    search_fields = ['title', 'description', 'reporter__user__username', 'reporter__user__email']
    readonly_fields = ['created_at', 'updated_at', 'resolved_at']
    list_per_page = 20
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'issue_type', 'priority', 'status')
        }),
        ('Relationships', {
            'fields': ('reporter', 'company')
        }),
        ('Attachments', {
            'fields': ('attachment', 'image'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'resolved_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('reporter', 'reporter__user', 'company')

@admin.register(IssueComment)
class IssueCommentAdmin(admin.ModelAdmin):
    list_display = ['issue', 'author', 'created_at', 'is_business_owner_note']
    list_filter = ['is_business_owner_note', 'created_at']
    search_fields = ['comment', 'issue__title', 'author__user__username']
    readonly_fields = ['created_at']
    list_per_page = 20
    
    fieldsets = (
        ('Comment Information', {
            'fields': ('issue', 'author', 'comment', 'is_business_owner_note')
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('issue', 'author', 'author__user')