from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from resume.models import Resume
from resume.enums import FileType, ProcessingStatus
import os
import io
import PyPDF2
from docx import Document
import chardet

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
        
        try:
            # Extract content from file in memory
            content = self.extract_content_from_file(resume_file, file_extension)
            
            # Create resume object without saving the file
            resume_obj = Resume.objects.create(
                user=user,
                file=None,  # Don't save the file
                original_filename=resume_file.name,
                file_type=file_extension,
                file_size=resume_file.size,
                parsed_content=content,  # Save the extracted content directly
                processing_status=ProcessingStatus.COMPLETED.value,
                is_processed=True
            )

            return Response({
                "message": "Resume processed successfully",
                "resume_id": resume_obj.id,
                "status": ProcessingStatus.COMPLETED.value,
                "file_type": file_extension,
                "file_type_display": FileType.get_display_name(file_extension),
                "file_size": resume_file.size,
                "content_length": len(content) if content else 0
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                "error": f"Error processing file: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)

    def extract_content_from_file(self, file_obj, file_extension):
        """Extract content from file object in memory"""
        try:
            if file_extension == FileType.PDF.value:
                return self.extract_pdf_text_from_memory(file_obj)
            elif file_extension in [FileType.DOC.value, FileType.DOCX.value]:
                return self.extract_word_text_from_memory(file_obj, file_extension)
            elif file_extension in [FileType.TXT.value, FileType.RTF.value]:
                return self.extract_text_file_from_memory(file_obj)
            else:
                return self.extract_generic_text_from_memory(file_obj)
        except Exception as e:
            raise Exception(f"Error extracting content: {str(e)}")

    def extract_pdf_text_from_memory(self, file_obj):
        """Extract text from PDF file in memory"""
        try:
            file_obj.seek(0)  # Reset file pointer
            pdf_reader = PyPDF2.PdfReader(file_obj)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"Error extracting PDF text: {str(e)}")

    def extract_word_text_from_memory(self, file_obj, file_extension):
        """Extract text from Word document in memory"""
        try:
            file_obj.seek(0)  # Reset file pointer
            if file_extension == FileType.DOCX.value:
                doc = Document(file_obj)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text.strip()
            else:
                # For .doc files, we'll need additional libraries
                return f"Word document (.doc) processing not yet implemented for {file_obj.name}"
        except Exception as e:
            raise Exception(f"Error extracting Word document text: {str(e)}")

    def extract_text_file_from_memory(self, file_obj):
        """Extract text from plain text file in memory"""
        try:
            file_obj.seek(0)  # Reset file pointer
            raw_data = file_obj.read()
            
            # Detect encoding
            detected = chardet.detect(raw_data)
            encoding = detected['encoding'] or 'utf-8'
            
            # Decode with detected encoding
            return raw_data.decode(encoding).strip()
        except Exception as e:
            raise Exception(f"Error extracting text file content: {str(e)}")

    def extract_generic_text_from_memory(self, file_obj):
        """Try to extract text from unknown file types in memory"""
        try:
            file_obj.seek(0)  # Reset file pointer
            raw_data = file_obj.read()
            
            # Try to decode with different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    content = raw_data.decode(encoding)
                    # Check if content looks like text (not too many null bytes)
                    if content.count('\x00') < len(content) * 0.1:
                        return content.strip()
                except UnicodeDecodeError:
                    continue
            
            # If all text encodings fail, return binary file info
            return f"Binary file detected. File size: {len(raw_data)} bytes. Text extraction not possible."
            
        except Exception as e:
            raise Exception(f"Error processing generic file: {str(e)}")

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

