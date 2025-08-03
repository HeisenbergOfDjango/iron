import os
import mimetypes
from celery import shared_task
from django.utils import timezone
from django.core.files.storage import default_storage
import PyPDF2
import io
from docx import Document
import chardet
from .enums import FileType, ProcessingStatus

@shared_task
def process_resume_file(resume_id):
    """
    Background task to process uploaded resume files of various formats
    """
    from .models import Resume
    
    try:
        resume = Resume.objects.get(id=resume_id)
        resume.processing_status = ProcessingStatus.PROCESSING.value
        resume.save()
        
        if not resume.file:
            raise Exception("No file found")
        
        # Get file information
        file_path = resume.file.path
        file_name = resume.original_filename
        file_extension = os.path.splitext(file_name)[1].lower()
        
        # Update file metadata
        resume.file_type = file_extension
        resume.file_size = resume.file.size
        resume.save()
        
        # Check if file type is supported
        if not FileType.is_supported(file_extension):
            raise Exception(f"Unsupported file type: {file_extension}. Supported types: {', '.join(FileType.get_supported_extensions())}")
        
        # Process based on file type
        content = ""
        
        if file_extension == FileType.PDF.value:
            content = extract_pdf_text(file_path)
        elif file_extension in [FileType.DOC.value, FileType.DOCX.value]:
            content = extract_word_text(file_path, file_extension)
        elif file_extension in [FileType.TXT.value, FileType.RTF.value]:
            content = extract_text_file(file_path)
        else:
            # Try to extract text from unknown file types
            content = extract_generic_text(file_path)
        
        # Update resume with extracted content
        resume.parsed_content = content
        resume.processing_status = ProcessingStatus.COMPLETED.value
        resume.is_processed = True
        resume.processed_at = timezone.now()
        resume.save()
        
        return f"Successfully processed {file_name}"
        
    except Exception as e:
        # Update resume with error information
        resume.processing_status = ProcessingStatus.FAILED.value
        resume.error_message = str(e)
        resume.save()
        raise e

def extract_pdf_text(file_path):
    """Extract text from PDF files"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        raise Exception(f"Error extracting PDF text: {str(e)}")

def extract_word_text(file_path, file_extension):
    """Extract text from Word documents"""
    try:
        if file_extension == FileType.DOCX.value:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        else:
            # For .doc files, we'll need additional libraries like python-docx2txt
            # For now, return a placeholder
            return f"Word document (.doc) processing not yet implemented for {os.path.basename(file_path)}"
    except Exception as e:
        raise Exception(f"Error extracting Word document text: {str(e)}")

def extract_text_file(file_path):
    """Extract text from plain text files"""
    try:
        # Detect encoding
        with open(file_path, 'rb') as file:
            raw_data = file.read()
            detected = chardet.detect(raw_data)
            encoding = detected['encoding'] or 'utf-8'
        
        # Read with detected encoding
        with open(file_path, 'r', encoding=encoding) as file:
            return file.read().strip()
    except Exception as e:
        raise Exception(f"Error extracting text file content: {str(e)}")

def extract_generic_text(file_path):
    """Try to extract text from unknown file types"""
    try:
        # Try to read as text with different encodings
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    content = file.read()
                    # Check if content looks like text (not too many null bytes)
                    if content.count('\x00') < len(content) * 0.1:
                        return content.strip()
            except UnicodeDecodeError:
                continue
        
        # If all text encodings fail, return binary file info
        file_size = os.path.getsize(file_path)
        return f"Binary file detected. File size: {file_size} bytes. Text extraction not possible."
        
    except Exception as e:
        raise Exception(f"Error processing generic file: {str(e)}")

@shared_task
def cleanup_failed_resumes():
    """Clean up resumes that failed processing after a certain time"""
    from .models import Resume
    from django.utils import timezone
    from datetime import timedelta
    
    # Delete resumes that failed more than 7 days ago
    cutoff_date = timezone.now() - timedelta(days=7)
    failed_resumes = Resume.objects.filter(
        processing_status=ProcessingStatus.FAILED.value,
        uploaded_at__lt=cutoff_date
    )
    
    count = failed_resumes.count()
    failed_resumes.delete()
    
    return f"Cleaned up {count} failed resumes"
