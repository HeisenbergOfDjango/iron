from enum import Enum

class FileType(Enum):
    """Supported file types for resume uploads"""
    PDF = '.pdf'
    DOCX = '.docx'
    DOC = '.doc'
    TXT = '.txt'
    RTF = '.rtf'
    
    @classmethod
    def get_supported_extensions(cls):
        """Get list of all supported file extensions"""
        return [file_type.value for file_type in cls]
    
    @classmethod
    def is_supported(cls, extension):
        """Check if a file extension is supported"""
        return extension.lower() in cls.get_supported_extensions()
    
    @classmethod
    def get_display_name(cls, extension):
        """Get human-readable name for file type"""
        mapping = {
            '.pdf': 'PDF Document',
            '.docx': 'Word Document (DOCX)',
            '.doc': 'Word Document (DOC)',
            '.txt': 'Text File',
            '.rtf': 'Rich Text Format'
        }
        return mapping.get(extension.lower(), 'Unknown File Type')

class ProcessingStatus(Enum):
    """Processing status for resume files"""
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    
    @classmethod
    def get_choices(cls):
        """Get choices for Django model field"""
        return [(status.value, status.value.title()) for status in cls]
    
    @classmethod
    def get_display_name(cls, status):
        """Get human-readable name for status"""
        mapping = {
            'pending': 'Pending',
            'processing': 'Processing',
            'completed': 'Completed',
            'failed': 'Failed'
        }
        return mapping.get(status, 'Unknown Status')

class QuestionCategory(Enum):
    """Categories for generated questions"""
    SKILLS = 'skills'
    EXPERIENCE = 'experience'
    INTERNSHIPS = 'internships'
    PROJECTS = 'projects'
    SOFT_SKILLS = 'soft_skills'
    HR = 'hr'
    
    @classmethod
    def get_choices(cls):
        """Get choices for Django model field"""
        mapping = {
            'skills': 'Technical Skills',
            'experience': 'Work Experience',
            'internships': 'Internships',
            'projects': 'Projects',
            'soft_skills': 'Soft Skills',
            'hr': 'HR Questions',
        }
        return [(category.value, mapping[category.value]) for category in cls]
    
    @classmethod
    def get_display_name(cls, category):
        """Get human-readable name for category"""
        mapping = {
            'skills': 'Technical Skills',
            'experience': 'Work Experience',
            'internships': 'Internships',
            'projects': 'Projects',
            'soft_skills': 'Soft Skills',
            'hr': 'HR Questions',
        }
        return mapping.get(category, 'Unknown Category')
