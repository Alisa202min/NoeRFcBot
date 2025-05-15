from app import db
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
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        """Set user password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check user password"""
        return check_password_hash(self.password_hash, password)


class ProductCategory(db.Model):
    """Category model for products"""
    __tablename__ = 'product_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('product_categories.id'), nullable=True)
    
    # Relationships
    children = db.relationship('ProductCategory', backref=db.backref('parent', remote_side=[id]))
    products = db.relationship('Product', backref='category', lazy='dynamic')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ProductCategory {self.name}>'


class ServiceCategory(db.Model):
    """Category model for services"""
    __tablename__ = 'service_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('service_categories.id'), nullable=True)
    
    # Relationships
    children = db.relationship('ServiceCategory', backref=db.backref('parent', remote_side=[id]))
    services = db.relationship('Service', backref='category', lazy='dynamic')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ServiceCategory {self.name}>'


class EducationalCategory(db.Model):
    """Category model for educational content"""
    __tablename__ = 'educational_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('educational_categories.id'), nullable=True)
    
    # Relationships
    children = db.relationship('EducationalCategory', backref=db.backref('parent', remote_side=[id]))
    contents = db.relationship('EducationalContent', backref='educational_category', lazy='dynamic')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<EducationalCategory {self.name}>'


# Legacy Category model has been removed - now using ProductCategory and ServiceCategory instead


class Product(db.Model):
    """Product model - now separate from services"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('product_categories.id'))
    photo_url = db.Column(db.Text, nullable=True)
    
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
    category_id = db.Column(db.Integer, db.ForeignKey('service_categories.id'))
    photo_url = db.Column(db.Text, nullable=True)
    
    # Media-related columns
    file_id = db.Column(db.Text, nullable=True)  # Main Telegram file_id
    video_url = db.Column(db.Text, nullable=True)
    video_file_id = db.Column(db.Text, nullable=True)
    
    # Service status columns
    featured = db.Column(db.Boolean, default=False)  # برای نمایش در صفحه اصلی
    available = db.Column(db.Boolean, default=True)  # وضعیت در دسترس بودن
    
    # Service-specific fields
    provider = db.Column(db.String(255), nullable=True)
    service_code = db.Column(db.String(255), nullable=True)
    duration = db.Column(db.String(255), nullable=True)
    tags = db.Column(db.Text, nullable=True)
    
    # Relationships
    media = db.relationship('ServiceMedia', backref='service', lazy='dynamic', cascade='all, delete-orphan')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    local_path = db.Column(db.String(255), nullable=True)  # Local path to file
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Media {self.id} for Service {self.service_id}>'


class Inquiry(db.Model):
    """Customer price inquiries for products and services"""
    __tablename__ = 'inquiries'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.BigInteger, nullable=False)  # Telegram user_id
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # Required in database
    status = db.Column(db.String(20), nullable=False, default='new')  # 'new', 'in_progress', 'completed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product = db.relationship('Product', foreign_keys=[product_id], backref='inquiries')
    service = db.relationship('Service', foreign_keys=[service_id], backref='inquiries')
    
    __table_args__ = (
        db.CheckConstraint('(product_id IS NOT NULL AND service_id IS NULL) OR '
                          '(product_id IS NULL AND service_id IS NOT NULL) OR '
                          '(product_id IS NULL AND service_id IS NULL)',
                          name='product_or_service_check'),
    )
    
    def __repr__(self):
        if self.product_id:
            return f'<ProductInquiry {self.id} - {self.name}>'
        elif self.service_id:
            return f'<ServiceInquiry {self.id} - {self.name}>'
        else:
            return f'<GeneralInquiry {self.id} - {self.name}>'
    
    def is_product_inquiry(self):
        """Check if this is a product inquiry"""
        return self.product_id is not None
    
    def is_service_inquiry(self):
        """Check if this is a service inquiry"""
        return self.service_id is not None
    
    @property
    def related_product(self):
        """For backward compatibility"""
        return self.product
        
    @property
    def related_service(self):
        """For backward compatibility"""
        return self.service


class EducationalContent(db.Model):
    """Educational content for the bot"""
    __tablename__ = 'educational_content'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text, nullable=False)
    # نگه داشتن فیلد category برای حفظ سازگاری با کد قبلی
    category = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('educational_categories.id'), nullable=True)
    content_type = db.Column(db.String(20), default='text')  # text, video, link, etc.
    type = db.Column(db.Text)  # Duplicate of content_type for backward compatibility
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    media = db.relationship('EducationalContentMedia', backref='content', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<EducationalContent {self.title}>'


class EducationalContentMedia(db.Model):
    """Media files for educational content"""
    __tablename__ = 'educational_content_media'
    
    id = db.Column(db.Integer, primary_key=True)
    educational_content_id = db.Column(db.Integer, db.ForeignKey('educational_content.id', ondelete='CASCADE'), nullable=False)
    file_id = db.Column(db.Text, nullable=False)  # Telegram file_id
    file_type = db.Column(db.String(10), default='photo')  # photo, video, etc.
    local_path = db.Column(db.Text, nullable=True)  # Local path to file
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<EducationalContentMedia {self.id} for EducationalContent {self.educational_content_id}>'


class StaticContent(db.Model):
    """Static content for About, Contact, etc."""
    __tablename__ = 'static_content'
    
    id = db.Column(db.Integer, primary_key=True)
    content_type = db.Column(db.String(20), nullable=False, unique=True)  # about, contact, etc.
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.Text)  # Duplicate of content_type for backward compatibility
    
    # Timestamps
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<StaticContent {self.content_type}>'