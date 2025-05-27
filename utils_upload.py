"""
Flask-Uploads extension modified to work with newer Werkzeug versions.
This fixes the "ImportError: cannot import name 'secure_filename' from 'werkzeug'" error.
"""

import os
import posixpath
from flask import Blueprint, Flask, current_app, request, abort, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

# This check ensures that the code will work with any versions
try:
    from werkzeug import FileStorage  # For compatibility with older Flask-Uploads
except ImportError:
    pass  # Already imported from werkzeug.datastructures

class UploadNotAllowed(Exception):
    """Exception raised if the upload is not allowed."""
    pass

class UploadSet:
    """This represents a set of uploads as defined by the user."""
    def __init__(self, name, extensions=None, default_dest=None):
        self.name = name
        self.extensions = extensions
        self.default_dest = default_dest

    def file_allowed(self, storage, basename=None):
        """
        Check if a file is allowed based on extension.
        """
        if basename is None:
            basename = storage.filename
        return self.extension_allowed(extension(basename))

    def extension_allowed(self, ext):
        """
        Check if an extension is allowed.
        """
        return (self.extensions is None or
                ext.lower() in self.extensions)

    def get_basename(self, filename):
        """
        Returns the basename for the provided filename.
        """
        return secure_filename(filename)

    def save(self, storage, folder=None, name=None):
        """
        Save a storage to disk.
        """
        if not isinstance(storage, FileStorage):
            raise TypeError("storage must be a werkzeug.FileStorage")

        if not self.file_allowed(storage):
            raise UploadNotAllowed()

        if name is not None:
            basename = name
            if '.' not in basename:
                basename = '%s.%s' % (basename, extension(storage.filename))
        else:
            basename = self.get_basename(storage.filename)

        if not basename:
            raise ValueError("Invalid filename: %s" % storage.filename)

        target_folder = self.get_path(folder)
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)

        target = os.path.join(target_folder, basename)
        storage.save(target)
        return basename

    def get_path(self, folder=None):
        """
        Get the absolute path for this upload set.
        """
        if folder is None:
            folder = self.default_dest
        
        config = current_app.config
        
        if folder:
            return os.path.join(config.get('UPLOADS_DEFAULT_DEST'), folder)
        
        return config.get('UPLOADS_DEFAULT_DEST')

    def url(self, filename):
        """
        Get the URL for a given filename.
        """
        folder = self.default_dest
        if folder is None:
            raise RuntimeError("No default folder specified for %r" % self)
        
        path = posixpath.normpath(posixpath.join(folder, filename))
        return path


# Common extensions
TEXT = ('txt',)
DOCUMENTS = tuple('rtf odf ods gnumeric abw doc docx xls xlsx'.split())
IMAGES = tuple('jpg jpe jpeg png gif svg bmp webp'.split())
AUDIO = tuple('wav mp3 aac ogg oga flac'.split())
DATA = tuple('csv ini json plist xml yaml yml'.split())
SCRIPTS = tuple('js php pl py rb sh'.split())
ARCHIVES = tuple('gz bz2 zip tar tgz txz 7z'.split())
EXECUTABLES = tuple('so exe dll'.split())
VIDEO = tuple('mp4 webm'.split())

# All available extension sets
DEFAULTS = {
    'text': TEXT,
    'documents': DOCUMENTS,
    'images': IMAGES,
    'audio': AUDIO,
    'data': DATA,
    'scripts': SCRIPTS,
    'archives': ARCHIVES,
    'executables': EXECUTABLES,
    'video': VIDEO
}


def configure_uploads(app, upload_sets):
    """
    Configure the upload sets for an application.
    """
    if isinstance(upload_sets, UploadSet):
        upload_sets = (upload_sets,)

    if not hasattr(app, 'upload_set_config'):
        app.upload_set_config = {}
    
    for uset in upload_sets:
        config_prefix = 'UPLOADED_%s_' % uset.name.upper()
        dest = os.path.join(app.config.get('UPLOADS_DEFAULT_DEST', 'uploads'),
                           uset.name)
        app.config.setdefault(config_prefix + 'DEST', dest)
        
        try:
            uset.default_dest = app.config[config_prefix + 'DEST']
        except KeyError:
            pass
    
    return app


def extension(filename):
    """
    Get the extension of a file.
    """
    return filename.rsplit('.', 1)[-1] if '.' in filename else ''


def addslash(url):
    """
    Add a trailing slash to a URL.
    """
    if url.endswith('/'):
        return url
    return url + '/'


def patch_request_class(app, size=None):
    """
    Patch the request class to set the max size (not implemented).
    """
    if size is not None:
        app.config['MAX_CONTENT_LENGTH'] = size
    return app


def is_valid_image(file_storage, max_size=5 * 1024 * 1024):
    """
    بررسی اعتبار تصویر آپلودی
    
    Args:
        file_storage: آبجکت FileStorage از werkzeug
        max_size: حداکثر سایز مجاز به بایت (پیش‌فرض 5MB)
        
    Returns:
        bool: True اگر تصویر معتبر باشد، False در غیر این صورت
    """
    from image_logger import log_file_validation
    
    if not file_storage:
        log_file_validation("No file", False, "No file provided")
        return False
    
    # بررسی نوع محتوا
    content_type = file_storage.content_type.lower()
    if not content_type.startswith('image/'):
        log_file_validation(file_storage.filename, False, f"Invalid content type: {content_type}")
        return False
    
    # بررسی سایز فایل
    file_storage.seek(0, os.SEEK_END)
    file_size = file_storage.tell()
    file_storage.seek(0)  # بازگرداندن اشاره‌گر فایل به ابتدا
    
    if file_size > max_size:
        log_file_validation(
            file_storage.filename, 
            False, 
            f"File too large: {file_size/1024/1024:.2f}MB > {max_size/1024/1024:.2f}MB"
        )
        return False
    
    # بررسی پسوند فایل
    filename = file_storage.filename
    ext = extension(filename).lower()
    
    if ext not in IMAGES:
        log_file_validation(file_storage.filename, False, f"Invalid extension: {ext}")
        return False
    
    # بررسی محتوای فایل به عنوان تصویر
    try:
        from PIL import Image
        img = Image.open(file_storage.stream)
        img.verify()  # اعتبارسنجی فرمت تصویر
        file_storage.seek(0)  # بازگرداندن اشاره‌گر فایل به ابتدا
        log_file_validation(file_storage.filename, True, "Image passed all validation checks")
        return True
    except Exception as e:
        log_file_validation(file_storage.filename, False, f"Image verification failed: {str(e)}")
        file_storage.seek(0)  # بازگرداندن اشاره‌گر فایل به ابتدا
        return False


def save_uploaded_file(file_storage, upload_folder, validate=False, max_size=5 * 1024 * 1024):
    """
    ذخیره فایل آپلودی با نام امن
    
    Args:
        file_storage: آبجکت FileStorage از werkzeug
        upload_folder: مسیر پوشه برای ذخیره فایل
        validate: اعتبارسنجی فایل به عنوان تصویر (True/False)
        max_size: حداکثر سایز مجاز به بایت (پیش‌فرض 5MB)
        
    Returns:
        str: نام فایل ذخیره شده یا None در صورت خطا
    """
    from image_logger import log_upload_start, log_upload_success, log_upload_error
    
    if not file_storage:
        log_upload_error("No file", "No file provided")
        return None
    
    # اعتبارسنجی فایل در صورت نیاز
    if validate and not is_valid_image(file_storage, max_size):
        log_upload_error(file_storage.filename, "File validation failed")
        return None
    
    try:
        # اطمینان از وجود پوشه آپلود
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder, exist_ok=True)
        
        # ایجاد نام امن فایل و مسیر نهایی
        filename = secure_filename(file_storage.filename)
        if not filename:
            log_upload_error(file_storage.filename, "Invalid filename")
            return None
        
        # افزودن تایم‌استمپ به نام فایل برای جلوگیری از تداخل
        import time
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{int(time.time())}{ext}"
        
        file_path = os.path.join(upload_folder, unique_filename)
        
        # ذخیره فایل
        file_storage.save(file_path)
        
        log_upload_success(file_storage.filename, file_path)
        return unique_filename
    
    except Exception as e:
        log_upload_error(file_storage.filename, str(e))
        import traceback
        traceback.print_exc()
        return None


def find_file_in_static_dirs(filename, static_dirs=None):
    """
    جستجوی فایل در مسیرهای استاتیک
    
    Args:
        filename: نام فایل برای جستجو
        static_dirs: لیست مسیرهای استاتیک برای جستجو (پیش‌فرض: ['static', 'static/uploads'])
        
    Returns:
        str: مسیر کامل فایل یا None اگر پیدا نشد
    """
    from image_logger import log_file_not_found
    
    if not filename:
        return None
    
    if static_dirs is None:
        static_dirs = ['static', 'static/uploads', 'static/images', 'uploads']
    
    # حذف '/' از ابتدای نام فایل
    if filename.startswith('/'):
        filename = filename[1:]
    
    # حذف 'static/' از ابتدای نام فایل
    if filename.startswith('static/'):
        filename = filename[7:]
    
    # جستجو در همه مسیرهای استاتیک
    for static_dir in static_dirs:
        file_path = os.path.join(static_dir, filename)
        if os.path.exists(file_path):
            return file_path
    
    log_file_not_found(filename)
    return None