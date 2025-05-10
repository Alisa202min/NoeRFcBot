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