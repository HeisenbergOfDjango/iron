from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from resume.models import Resume
from resume.tasks import process_resume_file
from resume.enums import FileType, ProcessingStatus
import os

# Create your views here.

class ResumeUploadView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, **kwargs):
        user = request.user
        resume_file = request.FILES.get('resume')

        if not resume_file:
            return Response(
                {"error": "No file provided"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate file size (e.g., max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if resume_file.size > max_size:
            return Response(
                {"error": "File size too large. Maximum size is 10MB"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get file extension and validate
        file_extension = os.path.splitext(resume_file.name)[1].lower()
        
        if not FileType.is_supported(file_extension):
            supported_types = FileType.get_supported_extensions()
            return Response({
                "error": f"Unsupported file type: {file_extension}",
                "supported_types": supported_types,
                "supported_types_display": [FileType.get_display_name(ext) for ext in supported_types]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create resume object
        resume_obj = Resume.objects.create(
            user=user,
            file=resume_file,
            original_filename=resume_file.name,
            file_type=file_extension,
            file_size=resume_file.size,
            processing_status=ProcessingStatus.PENDING.value
        )

        # Start background processing
        process_resume_file.delay(resume_obj.id)

        return Response({
            "message": "Resume uploaded successfully",
            "resume_id": resume_obj.id,
            "status": ProcessingStatus.PENDING.value,
            "file_type": file_extension,
            "file_type_display": FileType.get_display_name(file_extension),
            "file_size": resume_file.size
        }, status=status.HTTP_201_CREATED)

class ResumeStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, resume_id, **kwargs):
        try:
            resume = Resume.objects.get(id=resume_id, user=request.user)
            
            response_data = {
                "resume_id": resume.id,
                "filename": resume.original_filename,
                "file_type": resume.file_type,
                "file_type_display": FileType.get_display_name(resume.file_type) if resume.file_type else None,
                "file_size": resume.file_size,
                "status": resume.processing_status,
                "status_display": ProcessingStatus.get_display_name(resume.processing_status),
                "uploaded_at": resume.uploaded_at,
                "processed_at": resume.processed_at,
                "is_processed": resume.is_processed
            }
            
            if resume.processing_status == ProcessingStatus.COMPLETED.value:
                response_data["content_preview"] = resume.parsed_content[:500] + "..." if len(resume.parsed_content) > 500 else resume.parsed_content
            elif resume.processing_status == ProcessingStatus.FAILED.value:
                response_data["error_message"] = resume.error_message
                
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Resume.DoesNotExist:
            return Response(
                {"error": "Resume not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

class ResumeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, **kwargs):
        resumes = Resume.objects.filter(user=request.user)
        
        resume_list = []
        for resume in resumes:
            resume_data = {
                "id": resume.id,
                "filename": resume.original_filename,
                "file_type": resume.file_type,
                "file_type_display": FileType.get_display_name(resume.file_type) if resume.file_type else None,
                "status": resume.processing_status,
                "status_display": ProcessingStatus.get_display_name(resume.processing_status),
                "uploaded_at": resume.uploaded_at,
                "is_processed": resume.is_processed
            }
            resume_list.append(resume_data)
            
        return Response({
            "resumes": resume_list,
            "count": len(resume_list)
        }, status=status.HTTP_200_OK)

class SupportedFileTypesView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, **kwargs):
        """Get list of supported file types"""
        supported_types = FileType.get_supported_extensions()
        supported_types_info = []
        
        for ext in supported_types:
            supported_types_info.append({
                "extension": ext,
                "display_name": FileType.get_display_name(ext)
            })
            
        return Response({
            "supported_file_types": supported_types_info,
            "count": len(supported_types)
        }, status=status.HTTP_200_OK)

