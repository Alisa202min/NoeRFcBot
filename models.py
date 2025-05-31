from extensions import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy


class User(UserMixin, db.Model):
    """User model for admin authentication and Telegram users"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=True)
    password_hash = db.Column(db.String(256), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
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
    __tablename__ = 'product_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('product_categories.id'), nullable=True)
    parent = db.relationship('ProductCategory', remote_side=[id], backref=db.backref('children', lazy='dynamic'))

    def __repr__(self):
        return f'<ProductCategory {self.name}>'

class ServiceCategory(db.Model):
    __tablename__ = 'service_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('service_categories.id'), nullable=True)
    parent = db.relationship('ServiceCategory', remote_side=[id], backref=db.backref('children', lazy='dynamic'))

    def __repr__(self):
        return f'<ServiceCategory {self.name}>'

class EducationalCategory(db.Model):
    __tablename__ = 'educational_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('educational_categories.id'), nullable=True)
    parent = db.relationship('EducationalCategory', remote_side=[id], backref=db.backref('children', lazy='dynamic'))

    def __repr__(self):
        return f'<EducationalCategory {self.name}>'

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('product_categories.id'))
    category = db.relationship('ProductCategory', backref='products')  # اضافه شده
    brand = db.Column(db.Text, nullable=True)
    model = db.Column(db.String(64), nullable=True)
    in_stock = db.Column(db.Boolean, default=True)
    tags = db.Column(db.Text, nullable=True)
    featured = db.Column(db.Boolean, default=False)
    model_number = db.Column(db.Text, nullable=True)
    manufacturer = db.Column(db.Text, nullable=True)
    provider = db.Column(db.String(255), nullable=True)
    service_code = db.Column(db.String(255), nullable=True)
    duration = db.Column(db.String(255), nullable=True)
    media = db.relationship('ProductMedia', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Product {self.name}>'

class Service(db.Model):
    __tablename__ = 'services'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('service_categories.id'))
    featured = db.Column(db.Boolean, default=False)
    available = db.Column(db.Boolean, default=True)
    tags = db.Column(db.Text, nullable=True)
    media = db.relationship('ServiceMedia', backref='service', lazy='dynamic', cascade='all, delete-orphan')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Service {self.name}>'

class ProductMedia(db.Model):
    __tablename__ = 'product_media'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'))
    file_id = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(10), default='photo')
    local_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Media {self.id} for Product {self.product_id}>'

class ServiceMedia(db.Model):
    __tablename__ = 'service_media'

    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id', ondelete='CASCADE'))
    file_id = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(10), default='photo')
    local_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Media {self.id} for Service {self.service_id}>'

class Inquiry(db.Model):
    __tablename__ = 'inquiries'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.BigInteger, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='new')
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
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
            return f'<Inquiry {self.id} from {self.name}>'

    def is_product_inquiry(self):
        return self.product_id is not None and self.service_id is None

    def is_service_inquiry(self):
        return self.service_id is not None and self.product_id is None

    @property
    def related_product(self):
        return self.product

    @property
    def related_service(self):
        return self.service

    @property
    def product_type(self):
        if self.product_id:
            return 'محصول'
        elif self.service_id:
            return 'خدمت'
        else:
            return 'نامشخص'

class EducationalContent(db.Model):
    __tablename__ = 'educational_content'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('educational_categories.id'), nullable=True)
    tags = db.Column(db.String(128), nullable=True)
    featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    media = db.relationship('EducationalContentMedia', backref='educational_content', lazy='dynamic', cascade='all, delete-orphan')
    category = db.relationship('EducationalCategory', backref='educational_contents')

class EducationalContentMedia(db.Model):
    __tablename__ = 'educational_content_media'

    id = db.Column(db.Integer, primary_key=True)
    content_id = db.Column(db.Integer, db.ForeignKey('educational_content.id', ondelete='CASCADE'), nullable=False)
    file_id = db.Column(db.Text, nullable=False)
    file_type = db.Column(db.String(10), default='photo')
    local_path = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<EducationalContentMedia {self.id} for EducationalContent {self.content_id}>'

class StaticContent(db.Model):
    __tablename__ = 'static_content'

    id = db.Column(db.Integer, primary_key=True)
    content_type = db.Column(db.String(20), nullable=False, unique=True)
    content = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<StaticContent {self.content_type}>'