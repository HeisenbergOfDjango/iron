from django.urls import path
from .views import ResumeUploadView, ResumeStatusView, ResumeListView, SupportedFileTypesView

app_name = 'resume'

urlpatterns = [
    path(r'upload/', ResumeUploadView.as_view(), name='resume_upload'),
    path(r'status/<int:resume_id>/', ResumeStatusView.as_view(), name='resume_status'),
    path(r'list/', ResumeListView.as_view(), name='resume_list'),
    path(r'supported-types/', SupportedFileTypesView.as_view(), name='supported_file_types'),
] 