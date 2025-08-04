import os
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .enums import ProcessingStatus

@shared_task
def cleanup_failed_resumes():
    """Clean up resumes that failed processing after a certain time"""
    from .models import Resume
    
    # Delete resumes that failed more than 7 days ago
    cutoff_date = timezone.now() - timedelta(days=7)
    failed_resumes = Resume.objects.filter(
        processing_status=ProcessingStatus.FAILED.value,
        uploaded_at__lt=cutoff_date
    )
    
    count = failed_resumes.count()
    failed_resumes.delete()
    
    return f"Cleaned up {count} failed resumes"
