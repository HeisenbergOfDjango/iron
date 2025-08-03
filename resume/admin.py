from django.contrib import admin
from .models import Resume, JobPosition, GeneratedQuestion

# Register your models here.

@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ['user', 'original_filename', 'uploaded_at', 'is_processed']
    list_filter = ['is_processed', 'uploaded_at']
    search_fields = ['user__username', 'original_filename']
    readonly_fields = ['uploaded_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'file', 'original_filename')
        }),
        ('Processing Status', {
            'fields': ('is_processed', 'parsed_content')
        }),
        ('Timestamps', {
            'fields': ('uploaded_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(JobPosition)
class JobPositionAdmin(admin.ModelAdmin):
    list_display = ['title', 'department', 'is_active', 'created_at']
    list_filter = ['is_active', 'department', 'created_at']
    search_fields = ['title', 'description', 'department']
    readonly_fields = ['created_at']


@admin.register(GeneratedQuestion)
class GeneratedQuestionAdmin(admin.ModelAdmin):
    list_display = ['category', 'resume', 'job_position', 'priority', 'generated_at']
    list_filter = ['category', 'priority', 'generated_at']
    search_fields = ['question_text', 'resume__original_filename', 'job_position__title']
    readonly_fields = ['generated_at']
    
    # Limit the number of questions shown per page
    list_per_page = 50
