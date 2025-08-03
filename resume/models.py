from django.db import models
from django.contrib.auth.models import User
from .enums import ProcessingStatus, QuestionCategory

# Create your models here.

class Resume(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes')
    file = models.FileField(upload_to='resumes/', null=True, blank=True) # right now we are not using this field
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50, null=True, blank=True)  # pdf, doc, docx, txt, etc.
    file_size = models.IntegerField(null=True, blank=True)  # in bytes
    parsed_content = models.TextField(null=True, blank=True)
    processing_status = models.CharField(max_length=20, choices=ProcessingStatus.get_choices(), default=ProcessingStatus.PENDING.value)
    error_message = models.TextField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    is_processed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} - {self.original_filename}"
    
    class Meta:
        ordering = ['-uploaded_at']


class JobPosition(models.Model):
    title = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    department = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['title']


class GeneratedQuestion(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='questions')
    job_position = models.ForeignKey(JobPosition, on_delete=models.CASCADE, related_name='questions')
    category = models.CharField(max_length=20, choices=QuestionCategory.get_choices())
    question_text = models.TextField()
    priority = models.IntegerField(default=1)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.category}: {self.question_text[:50]}..."
    
    class Meta:
        ordering = ['category', 'priority']

