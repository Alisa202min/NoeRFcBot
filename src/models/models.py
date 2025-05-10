from src.web.app import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    """User model for admin authentication and Telegram users"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=True)
    password_hash = db.Column(db.String(256), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Telegram specific fields
    telegram_id = db.Column(db.BigInteger, unique=True, nullable=True)
    telegram_username = db.Column(db.String(64), nullable=True)
    first_name = db.Column(db.String(64), nullable=True)
    last_name = db.Column(db.String(64), nullable=True)
    phone = db.Column(db.String(15), nullable=True)
    language_code = db.Column(db.String(10), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        """Set user password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check user password"""
        return check_password_hash(self.password_hash, password)


class Category(db.Model):
    """Category model for products and services"""
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    cat_type = db.Column(db.String(10), default='product')  # product or service
    
    # Relationships
    children = db.relationship('Category', backref=db.backref('parent', remote_side=[id]))
    products = db.relationship('Product', backref='category', lazy='dynamic')
    services = db.relationship('Service', backref='category', lazy='dynamic')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Category {self.name}>'


class Product(db.Model):
    """Product model - now separate from services"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    photo_url = db.Column(db.Text, nullable=True)
    
    # Type field for compatibility with old code
    product_type = db.Column(db.Text, default='product')
    
    # Extended fields for better search
    brand = db.Column(db.Text, nullable=True)
    model = db.Column(db.String(64), nullable=True)
    in_stock = db.Column(db.Boolean, default=True)
    tags = db.Column(db.Text, nullable=True)
    featured = db.Column(db.Boolean, default=False)
    
    # Additional database columns that exist in the schema
    model_number = db.Column(db.Text, nullable=True)
    manufacturer = db.Column(db.Text, nullable=True)
    provider = db.Column(db.String(255), nullable=True)
    service_code = db.Column(db.String(255), nullable=True)
    duration = db.Column(db.String(255), nullable=True)
    
    # Media-related columns
    file_id = db.Column(db.Text, nullable=True)  # Main Telegram file_id
    video_url = db.Column(db.Text, nullable=True)
    video_file_id = db.Column(db.Text, nullable=True)
    
    # Relationships
    media = db.relationship('ProductMedia', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    inquiries = db.relationship('Inquiry', backref='product', lazy='dynamic')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Product {self.name}>'


class Service(db.Model):
    """Service model - now separate from products"""
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    photo_url = db.Column(db.Text, nullable=True)
    
    # Media-related columns
    file_id = db.Column(db.Text, nullable=True)  # Main Telegram file_id
    video_url = db.Column(db.Text, nullable=True)
    video_file_id = db.Column(db.Text, nullable=True)
    
    # Relationships
    media = db.relationship('ServiceMedia', backref='service', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Service {self.name}>'


class ProductMedia(db.Model):
    """Media files for products"""
    __tablename__ = 'product_media'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'))
    file_id = db.Column(db.String(255), nullable=False)  # Telegram file_id
    file_type = db.Column(db.String(10), default='photo')  # photo, video, etc.
    local_path = db.Column(db.String(255), nullable=True)  # Local path to file
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Media {self.id} for Product {self.product_id}>'


class ServiceMedia(db.Model):
    """Media files for services"""
    __tablename__ = 'service_media'
    
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id', ondelete='CASCADE'))
    file_id = db.Column(db.String(255), nullable=False)  # Telegram file_id
    file_type = db.Column(db.String(10), default='photo')  # photo, video, etc.
    
    def __repr__(self):
        return f'<Media {self.id} for Service {self.service_id}>'


class Inquiry(db.Model):
    """Price inquiries from users"""
    __tablename__ = 'inquiries'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    name = db.Column(db.String(64), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    description = db.Column(db.Text)
    product_type = db.Column(db.String(10), default='product')  # product or service
    status = db.Column(db.String(20), default='pending')  # pending, responded, completed
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='inquiries')
    
    def __repr__(self):
        return f'<Inquiry {self.id} from {self.name}>'


class EducationalContent(db.Model):
    """Educational content for the bot"""
    __tablename__ = 'educational_content'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.Text, nullable=False)
    content_type = db.Column(db.String(20), default='text')  # text, video, link, etc.
    type = db.Column(db.Text)  # Duplicate of content_type for backward compatibility
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Note: updated_at is removed as it doesn't exist in the database schema
    
    def __repr__(self):
        return f'<EducationalContent {self.title}>'


class StaticContent(db.Model):
    """Static content for About, Contact, etc."""
    __tablename__ = 'static_content'
    
    id = db.Column(db.Integer, primary_key=True)
    content_type = db.Column(db.String(20), nullable=False, unique=True)  # about, contact, etc.
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.Text)  # Duplicate of content_type for backward compatibility
    
    # Timestamps
    # Note: created_at is not in the database schema
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<StaticContent {self.content_type}>'