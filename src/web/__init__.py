"""
ماژول وب فلسک
این ماژول شامل برنامه فلسک و مسیرهای وب است.
"""

from .app import app, db, media_files

__all__ = [
    'app',
    'db',
    'media_files'
]