"""
ماژول مدل‌های پایگاه داده
این ماژول شامل کلاس‌های مدل SQLAlchemy و لایه انتزاعی دیتابیس است.
"""

# Note: models.py has been moved to the root directory
# Import Database from root since database.py was also moved to root
try:
    from database import Database
except ImportError:
    # Fallback for when running from different contexts
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from database import Database

__all__ = [
    'Database'
]