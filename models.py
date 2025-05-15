"""
Database models for RFCBot
This module defines all SQLAlchemy models for the application
"""

import os
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import db

# User model
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Category model
class Category(db.Model):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey('categories.id', ondelete='CASCADE'), nullable=True)
    type = Column(String(20), default='product')  # 'product' or 'service'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    parent = relationship('Category', remote_side=[id], backref='children')
    products = relationship('Product', back_populates='category', cascade='all, delete-orphan')
    services = relationship('Service', back_populates='category', cascade='all, delete-orphan')

# Product model
class Product(db.Model):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    price = Column(Integer, default=0)
    description = Column(Text, nullable=True)
    brand = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    in_stock = Column(Boolean, default=True)
    featured = Column(Boolean, default=False)
    tags = Column(String(255), nullable=True)
    photo_url = Column(String(255), nullable=True)
    category_id = Column(Integer, ForeignKey('categories.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    category = relationship('Category', back_populates='products')
    media = relationship('ProductMedia', back_populates='product', cascade='all, delete-orphan')
    inquiries = relationship('Inquiry', back_populates='product', cascade='all, delete-orphan')

# ProductMedia model
class ProductMedia(db.Model):
    __tablename__ = 'product_media'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    file_id = Column(String(255), nullable=False)
    file_type = Column(String(20), default='photo')  # 'photo', 'video', etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    
    product = relationship('Product', back_populates='media')

# Service model
class Service(db.Model):
    __tablename__ = 'services'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    price = Column(Integer, default=0)
    description = Column(Text, nullable=True)
    featured = Column(Boolean, default=False)
    tags = Column(String(255), nullable=True)
    photo_url = Column(String(255), nullable=True)
    category_id = Column(Integer, ForeignKey('categories.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    category = relationship('Category', back_populates='services')
    media = relationship('ServiceMedia', back_populates='service', cascade='all, delete-orphan')
    inquiries = relationship('Inquiry', back_populates='service', cascade='all, delete-orphan')

# ServiceMedia model
class ServiceMedia(db.Model):
    __tablename__ = 'service_media'
    
    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey('services.id', ondelete='CASCADE'), nullable=False)
    file_id = Column(String(255), nullable=False)
    file_type = Column(String(20), default='photo')  # 'photo', 'video', etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    
    service = relationship('Service', back_populates='media')

# Inquiry model
class Inquiry(db.Model):
    __tablename__ = 'inquiries'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)  # Telegram user ID
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='SET NULL'), nullable=True)
    service_id = Column(Integer, ForeignKey('services.id', ondelete='SET NULL'), nullable=True)
    status = Column(String(20), default='pending')  # 'pending', 'processed', 'rejected'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    product = relationship('Product', back_populates='inquiries')
    service = relationship('Service', back_populates='inquiries')

# Educational category model
class EducationalCategory(db.Model):
    __tablename__ = 'educational_categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey('educational_categories.id', ondelete='CASCADE'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    parent = relationship('EducationalCategory', remote_side=[id], backref='children')
    contents = relationship('EducationalContent', back_populates='category', cascade='all, delete-orphan')

# Educational content model
class EducationalContent(db.Model):
    __tablename__ = 'educational_content'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)  # Legacy category field (just a string)
    category_id = Column(Integer, ForeignKey('educational_categories.id', ondelete='SET NULL'), nullable=True)
    content_type = Column(String(50), nullable=False)  # 'article', 'tutorial', 'video', etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # New relationship to hierarchical category
    category_rel = relationship('EducationalCategory', back_populates='contents')
    media = relationship('EducationalContentMedia', back_populates='content', cascade='all, delete-orphan')

# Educational content media model
class EducationalContentMedia(db.Model):
    __tablename__ = 'educational_content_media'
    
    id = Column(Integer, primary_key=True)
    content_id = Column(Integer, ForeignKey('educational_content.id', ondelete='CASCADE'), nullable=False)
    file_id = Column(String(255), nullable=False)
    file_type = Column(String(20), default='photo')  # 'photo', 'video', 'document', etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    
    content = relationship('EducationalContent', back_populates='media')

# Static content model (for contact info, about us, etc.)
class StaticContent(db.Model):
    __tablename__ = 'static_content'
    
    id = Column(Integer, primary_key=True)
    content_type = Column(String(50), unique=True, nullable=False)  # 'contact', 'about', etc.
    content = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)