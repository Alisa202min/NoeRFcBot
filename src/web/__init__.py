# Import app from app module
from .app import app, db

# Make modules available for import
__all__ = ['app', 'db']