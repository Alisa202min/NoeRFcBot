"""
ماژول وب فلسک
این ماژول شامل برنامه فلسک و مسیرهای وب است.
"""

# Import from the merged app.py in root directory
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app import app, db, media_files

__all__ = [
    'app',
    'db',
    'media_files'
]