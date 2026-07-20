"""
File security utilities for safe file handling
"""
import os
from pathlib import Path
# from werkzeug.utils import secure_filename
# Use simple filename sanitization instead
def secure_filename(filename):
    """Simple filename sanitization"""
    import re
    filename = re.sub(r'[^\w\s.-]', '', filename).strip()
    filename = re.sub(r'[-\s]+', '-', filename)
    return filename

ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def validate_file(uploaded_file):
    """Validate uploaded file for security and size"""
    if not uploaded_file:
        return False
    
    # Check file size
    if uploaded_file.size > MAX_FILE_SIZE:
        return False
    
    # Check file extension
    file_ext = Path(uploaded_file.name).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return False
    
    return True

def is_safe_path(path):
    """Check if path is safe (no path traversal)"""
    # Normalize path and check for traversal attempts
    normalized = os.path.normpath(path)
    
    # Check for path traversal patterns
    if '..' in normalized or normalized.startswith('/') or ':' in normalized:
        return False
    
    return True

def secure_file_path(base_dir, filename):
    """Create secure file path within base directory"""
    secure_name = secure_filename(filename)
    if not secure_name:
        return None
    
    file_path = Path(base_dir) / secure_name
    
    # Ensure path is within base directory
    try:
        file_path.resolve().relative_to(Path(base_dir).resolve())
        return file_path
    except ValueError:
        return None
