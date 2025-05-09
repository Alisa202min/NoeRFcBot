from app import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    """User model for admin authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Category(db.Model):
    """Category model for products and services"""
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    cat_type = db.Column(db.String(20), nullable=False)  # 'product' or 'service'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    parent = db.relationship('Category', remote_side=[id], backref='subcategories')
    products = db.relationship('Product', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'


class Product(db.Model):
    """Product/Service model"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=True)
    photo_url = db.Column(db.String(255), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    product_type = db.Column(db.String(20), nullable=False, default='product')  # 'product' or 'service'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    media_files = db.relationship('ProductMedia', backref='product', lazy=True, cascade="all, delete-orphan")
    inquiries = db.relationship('Inquiry', backref='product', lazy=True)
    
    def __repr__(self):
        return f'<Product {self.name}>'


class ProductMedia(db.Model):
    """Media files (photos/videos) for products and services"""
    __tablename__ = 'product_media'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    file_id = db.Column(db.String(255), nullable=False)  # Telegram file_id
    file_type = db.Column(db.String(10), nullable=False)  # 'photo' or 'video'
    local_path = db.Column(db.String(255), nullable=True)  # Path to local file if saved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ProductMedia {self.id} - {self.file_type}>'


class Inquiry(db.Model):
    """Customer price inquiries"""
    __tablename__ = 'inquiries'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.BigInteger, nullable=False)  # Telegram user_id
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    product_type = db.Column(db.String(20), nullable=False, default='product')  # 'product' or 'service'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Inquiry {self.id} - {self.name}>'


class EducationalContent(db.Model):
    """Educational content model"""
    __tablename__ = 'educational_content'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    content_type = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<EducationalContent {self.title}>'


class StaticContent(db.Model):
    """Static content for about/contact pages"""
    __tablename__ = 'static_content'
    
    id = db.Column(db.Integer, primary_key=True)
    content_type = db.Column(db.String(20), nullable=False, unique=True)  # 'about' or 'contact'
    content = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<StaticContent {self.content_type}>'