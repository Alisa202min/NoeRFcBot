"""
Flask-Uploads extension modified to work with newer Werkzeug versions.
This fixes the "ImportError: cannot import name 'secure_filename' from 'werkzeug'" error.
"""

import os
import posixpath
import time
from flask import current_app, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

try:
    from werkzeug import FileStorage
except ImportError:
    pass

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
        if basename is None:
            basename = storage.filename
        return self.extension_allowed(extension(basename))

    def extension_allowed(self, ext):
        return (self.extensions is None or ext.lower() in self.extensions)

    def get_basename(self, filename):
        return secure_filename(filename)

    def save(self, storage, folder=None, name=None):
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
        if folder is None:
            folder = self.default_dest

        config = current_app.config

        if folder:
            return os.path.join(config.get('UPLOADS_DEFAULT_DEST'), folder)

        return config.get('UPLOADS_DEFAULT_DEST')

    def url(self, filename):
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

# تعریف media_files
media_files = UploadSet('media', IMAGES + VIDEO)

def configure_uploads(app, upload_sets):
    if isinstance(upload_sets, UploadSet):
        upload_sets = (upload_sets,)

    if not hasattr(app, 'upload_set_config'):
        app.upload_set_config = {}

    for uset in upload_sets:
        config_prefix = 'UPLOADED_%s_' % uset.name.upper()
        dest = os.path.join(app.config.get('UPLOADS_DEFAULT_DEST', 'uploads'), uset.name)
        app.config.setdefault(config_prefix + 'DEST', dest)

        try:
            uset.default_dest = app.config[config_prefix + 'DEST']
        except KeyError:
            pass

    return app

def extension(filename):
    return filename.rsplit('.', 1)[-1] if '.' in filename else ''

def addslash(url):
    if url.endswith('/'):
        return url
    return url + '/'

def patch_request_class(app, size=None):
    if size is not None:
        app.config['MAX_CONTENT_LENGTH'] = size
    return app

def is_valid_image(file_storage, max_size=5 * 1024 * 1024):
    from image_logger import log_file_validation

    if not file_storage:
        log_file_validation("No file", False, "No file provided")
        return False

    content_type = file_storage.content_type.lower()
    if not content_type.startswith('image/'):
        log_file_validation(file_storage.filename, False, f"Invalid content type: {content_type}")
        return False

    file_storage.seek(0, os.SEEK_END)
    file_size = file_storage.tell()
    file_storage.seek(0)

    if file_size > max_size:
        log_file_validation(
            file_storage.filename, 
            False, 
            f"File too large: {file_size/1024/1024:.2f}MB > {max_size/1024/1024:.2f}MB"
        )
        return False

    filename = file_storage.filename
    ext = extension(filename).lower()

    if ext not in IMAGES:
        log_file_validation(file_storage.filename, False, f"Invalid extension: {ext}")
        return False

    try:
        from PIL import Image
        img = Image.open(file_storage.stream)
        img.verify()
        file_storage.seek(0)
        log_file_validation(file_storage.filename, True, "Image passed all validation checks")
        return True
    except Exception as e:
        log_file_validation(file_storage.filename, False, f"Image verification failed: {str(e)}")
        file_storage.seek(0)
        return False

def save_uploaded_file(file_storage, upload_folder, validate=False, max_size=5 * 1024 * 1024):
    from image_logger import log_upload_start, log_upload_success, log_upload_error

    if not file_storage:
        log_upload_error("No file", "No file provided")
        return None

    if validate and not is_valid_image(file_storage, max_size):
        log_upload_error(file_storage.filename, "File validation failed")
        return None

    try:
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder, exist_ok=True)

        filename = secure_filename(file_storage.filename)
        if not filename:
            log_upload_error(file_storage.filename, "Invalid filename")
            return None

        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{int(time.time())}{ext}"
        file_path = os.path.join(upload_folder, unique_filename)

        file_storage.save(file_path)
        log_upload_success(file_storage.filename, file_path)
        return unique_filename
    except Exception as e:
        log_upload_error(file_storage.filename, str(e))
        return None

def find_file_in_static_dirs(filename, static_dirs=None):
    from image_logger import log_file_not_found

    if not filename:
        return None

    if static_dirs is None:
        static_dirs = ['static', 'static/uploads', 'static/images', 'uploads']

    if filename.startswith('/'):
        filename = filename[1:]

    if filename.startswith('static/'):
        filename = filename[7:]

    for static_dir in static_dirs:
        file_path = os.path.join(static_dir, filename)
        if os.path.exists(file_path):
            return file_path

    log_file_not_found(filename)
    return None

def handle_media_upload(file, directory, file_type, custom_filename=None):
    """
    مدیریت آپلود فایل رسانه‌ای

    Args:
        file: فایل آپلودشده
        directory: دایرکتوری مقصد
        file_type: نوع فایل (مثل 'photo' یا 'video')
        custom_filename: نام فایل سفارشی (اختیاری)

    Returns:
        tuple: (موفقیت, مسیر فایل)
    """
    try:
        if not file or not file.filename:
            return False, None

        os.makedirs(directory, exist_ok=True)

        filename = secure_filename(custom_filename or file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{int(time.time())}{ext}"
        file_path = os.path.join(directory, unique_filename)

        file.save(file_path)
        return True, file_path
    except Exception as e:
        return False, None

def remove_file(file_path):
    """
    حذف فایل از سیستم فایل

    Args:
        file_path: مسیر فایل برای حذف

    Returns:
        bool: موفقیت یا عدم موفقیت
    """
    try:
        if file_path and os.path.isfile(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception:
        return False

def serve_file(filename):
    """
    ارائه فایل‌های رسانه‌ای

    Args:
        filename: نام فایل

    Returns:
        Response: پاسخ ارائه فایل
    """
    try:
        return send_from_directory('static/uploads', filename)
    except Exception as e:
        return None