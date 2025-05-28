"""
ماژول مدل‌های دیتابیس
این ماژول شامل مدل‌های SQLAlchemy برای برنامه است.
"""

from .models import (
    db,
    User,
    Product,
    ProductMedia,
    Service,
    ServiceMedia,
    Inquiry,
    EducationalContent,
    EducationalContentMedia,
    StaticContent,
    ProductCategory,
    ServiceCategory,
    EducationalCategory
)

__all__ = [
    'db',
    'User',
    'Product',
    'ProductMedia',
    'Service',
    'ServiceMedia',
    'Inquiry',
    'EducationalContent',
    'EducationalContentMedia',
    'StaticContent',
    'ProductCategory',
    'ServiceCategory',
    'EducationalCategory'
]