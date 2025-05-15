"""
Database module initialization
This module serves as a centralized place for database configuration
to avoid circular import issues between app.py and models.py
"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Create base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Create a single SQLAlchemy instance to be used across the application
db = SQLAlchemy(model_class=Base)

# Import database models to register them
# Note: This is done at the end to avoid circular imports
def initialize_models():
    """Import models to ensure they're registered with SQLAlchemy"""
    try:
        # pylint: disable=unused-import, import-outside-toplevel
        from models import User, Category, Product, ProductMedia, Service, ServiceMedia
        from models import Inquiry, EducationalCategory, EducationalContent, EducationalContentMedia
        # pylint: enable=unused-import
        return True
    except ImportError as e:
        import logging
        logging.error(f"Error importing models: {e}")
        return False