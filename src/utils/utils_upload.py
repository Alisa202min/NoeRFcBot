"""
توابع کمکی برای آپلود، مدیریت و نمایش فایل‌ها
"""

import os
import logging
from typing import Tuple, List, Dict, Optional
from werkzeug.utils import secure_filename
from flask import current_app, send_from_directory

# Define constants for file types
IMAGES = ('jpg', 'jpe', 'jpeg', 'png', 'gif', 'svg', 'bmp', 'webp')
VIDEO = ('mp4', 'mov', 'avi', 'webm')

# Allowed media types
ALLOWED_MEDIA_TYPES = ['photo', 'video']

# Configure logging
logger = logging.getLogger(__name__)

# Simple UploadSet replacement
class UploadSet:
    """A simplified implementation of UploadSet functionality"""
    
    def __init__(self, name, extensions=None):
        self.name = name
        self.extensions = extensions
        
    def save(self, storage, folder=None, name=None):
        """Save a file."""
        if not storage:
            return None
            
        filename = secure_filename(storage.filename)
        if name:
            filename = secure_filename(name)
            # Keep the file extension
            if '.' in storage.filename:
                ext = storage.filename.rsplit('.', 1)[1]
                if not filename.endswith('.' + ext):
                    filename = filename + '.' + ext
                    
        path = os.path.join(current_app.config.get('UPLOADS_DEFAULT_DEST', 'uploads'), 
                           self.name, folder or '')
        
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
            
        target = os.path.join(path, filename)
        storage.save(target)
        return filename
        
    def path(self, filename, folder=None):
        """Return absolute path to the file."""
        base_path = os.path.join(current_app.config.get('UPLOADS_DEFAULT_DEST', 'uploads'), 
                                self.name, folder or '')
        return os.path.join(base_path, filename)
        
def configure_uploads(app, upload_sets):
    """A simplified implementation of configure_uploads functionality"""
    if not hasattr(app, 'uploads_configured'):
        app.uploads_configured = True
        
    app.config.setdefault('UPLOADS_DEFAULT_DEST', os.path.join(app.instance_path, 'uploads'))
    
    # Make sure we have the upload folder
    os.makedirs(app.config['UPLOADS_DEFAULT_DEST'], exist_ok=True)
    
    # Register upload_sets with the app
    if not hasattr(app, 'upload_sets'):
        app.upload_sets = {}
        
    if isinstance(upload_sets, UploadSet):
        upload_sets = (upload_sets,)
        
    for upload_set in upload_sets:
        app.upload_sets[upload_set.name] = upload_set

def handle_media_upload(file, directory: str, file_type: str = 'photo', 
                       custom_filename: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Handle media file upload (photos/videos)
    
    Args:
        file: The uploaded file object
        directory: Upload directory
        file_type: Type of media (photo/video)
        custom_filename: Optional custom filename
        
    Returns:
        (success, file_path) tuple
    """
    try:
        # Check if file exists and is allowed
        if not file or not allowed_media_type(file, file_type):
            logger.warning(f"Invalid file or file type: {file}")
            return False, None
        
        # Ensure directory exists
        os.makedirs(directory, exist_ok=True)
        
        # Use custom filename or secure the original
        if custom_filename:
            filename = secure_filename(custom_filename)
            # Make sure extension is preserved
            if '.' in file.filename:
                ext = file.filename.rsplit('.', 1)[1].lower()
                if not filename.endswith(f".{ext}"):
                    filename = f"{filename}.{ext}"
        else:
            filename = secure_filename(file.filename)
        
        # Create full file path
        file_path = os.path.join(directory, filename)
        
        # Save the file
        file.save(file_path)
        
        logger.info(f"File uploaded successfully: {file_path}")
        return True, file_path
    except Exception as e:
        logger.error(f"Error in file upload: {e}")
        return False, None

def allowed_media_type(file, file_type: str) -> bool:
    """
    Check if file is allowed for the given media type
    
    Args:
        file: The file to check
        file_type: Type of media (photo/video)
        
    Returns:
        True if file is allowed, False otherwise
    """
    if not file or not file.filename or '.' not in file.filename:
        return False
    
    extension = file.filename.rsplit('.', 1)[1].lower()
    
    if file_type == 'photo':
        return extension in ['jpg', 'jpeg', 'png', 'gif']
    elif file_type == 'video':
        return extension in ['mp4', 'mov', 'avi']
    
    return False

def remove_file(file_path: str) -> bool:
    """
    Remove a file from the filesystem
    
    Args:
        file_path: Path to the file to remove
        
    Returns:
        True if file was removed, False otherwise
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"File removed: {file_path}")
            return True
        else:
            logger.warning(f"File not found: {file_path}")
            return False
    except Exception as e:
        logger.error(f"Error removing file: {e}")
        return False

def serve_file(directory: str, filename: str):
    """
    Serve a file from a directory
    
    Args:
        directory: Directory containing the file
        filename: Name of the file to serve
        
    Returns:
        Flask response with the file
    """
    return send_from_directory(directory, filename)