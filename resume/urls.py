from django.urls import path
from .views import ResumeUploadView, ResumeStatusView, ResumeListView, SupportedFileTypesView

app_name = 'resume'

urlpatterns = [
    path('upload/', ResumeUploadView.as_view(), name='resume_upload'),
    path('status/<int:resume_id>/', ResumeStatusView.as_view(), name='resume_status'),
    path('list/', ResumeListView.as_view(), name='resume_list'),
    path('supported-types/', SupportedFileTypesView.as_view(), name='supported_file_types'),
] 