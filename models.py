# models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, BigInteger, CheckConstraint
from sqlalchemy.orm import relationship, DeclarativeBase
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Base(DeclarativeBase):
    pass

class User(UserMixin, Base):
    """User model for admin authentication and Telegram users"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(120), nullable=True)
    password_hash = Column(String(256), nullable=True)
    is_admin = Column(Boolean, default=False)
    telegram_id = Column(BigInteger, unique=True, nullable=True)
    telegram_username = Column(String(64), nullable=True)
    first_name = Column(String(64), nullable=True)
    last_name = Column(String(64), nullable=True)
    phone = Column(String(15), nullable=True)
    language_code = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password):
        """Set user password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check user password"""
        return check_password_hash(self.password_hash, password)

class ProductCategory(Base):
    __tablename__ = 'product_categories'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    parent_id = Column(Integer, ForeignKey('product_categories.id'), nullable=True)
    parent = relationship('ProductCategory', remote_side=[id], backref='children')

    def __repr__(self):
        return f'<ProductCategory {self.name}>'

class ServiceCategory(Base):
    __tablename__ = 'service_categories'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    parent_id = Column(Integer, ForeignKey('service_categories.id'), nullable=True)
    parent = relationship('ServiceCategory', remote_side=[id], backref='children')

    def __repr__(self):
        return f'<ServiceCategory {self.name}>'

class EducationalCategory(Base):
    __tablename__ = 'educational_categories'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    parent_id = Column(Integer, ForeignKey('educational_categories.id'), nullable=True)
    parent = relationship('EducationalCategory', remote_side=[id], backref='children')

    def __repr__(self):
        return f'<EducationalCategory {self.name}>'

class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
    price = Column(Integer, default=0)
    category_id = Column(Integer, ForeignKey('product_categories.id'))
    category = relationship('ProductCategory', backref='products')
    brand = Column(Text, nullable=True)
    model = Column(String(64), nullable=True)
    in_stock = Column(Boolean, default=True)
    tags = Column(Text, nullable=True)
    featured = Column(Boolean, default=False)
    model_number = Column(Text, nullable=True)
    manufacturer = Column(Text, nullable=True)
    provider = Column(String(255), nullable=True)
    service_code = Column(String(255), nullable=True)
    duration = Column(String(255), nullable=True)
    media = relationship('ProductMedia', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Product {self.name}>'

class Service(Base):
    __tablename__ = 'services'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
    price = Column(Integer, default=0)
    category_id = Column(Integer, ForeignKey('service_categories.id'))
    category = relationship('ServiceCategory', backref='services')
    featured = Column(Boolean, default=False)
    available = Column(Boolean, default=True)
    tags = Column(Text, nullable=True)
    media = relationship('ServiceMedia', backref='service', lazy='dynamic', cascade='all, delete-orphan')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Service {self.name}>'

class ProductMedia(Base):
    __tablename__ = 'product_media'

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'))
    file_id = Column(String(255), nullable=False)
    file_type = Column(String(10), default='photo')
    local_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Media {self.id} for Product {self.product_id}>'

class ServiceMedia(Base):
    __tablename__ = 'service_media'

    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey('services.id', ondelete='CASCADE'))
    file_id = Column(String(255), nullable=False)
    file_type = Column(String(10), default='photo')
    local_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Media {self.id} for Service {self.service_id}>'

class Inquiry(Base):
    __tablename__ = 'inquiries'

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=True)
    service_id = Column(Integer, ForeignKey('services.id'), nullable=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default='new')
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    product = relationship('Product', foreign_keys=[product_id], backref='inquiries')
    service = relationship('Service', foreign_keys=[service_id], backref='inquiries')

    __table_args__ = (
        CheckConstraint('(product_id IS NOT NULL AND service_id IS NULL) OR '
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

class EducationalContent(Base):
    __tablename__ = 'educational_content'
    id = Column(Integer, primary_key=True)
    title = Column(String(128), nullable=False)
    content = Column(Text, nullable=False)
    category_id = Column(Integer, ForeignKey('educational_categories.id'), nullable=True)
    tags = Column(String(128), nullable=True)
    featured = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    media = relationship('EducationalContentMedia', backref='educational_content', lazy='dynamic', cascade='all, delete-orphan')
    category = relationship('EducationalCategory', backref='educational_contents')

class EducationalContentMedia(Base):
    __tablename__ = 'educational_content_media'

    id = Column(Integer, primary_key=True)
    content_id = Column(Integer, ForeignKey('educational_content.id', ondelete='CASCADE'), nullable=False)
    file_id = Column(Text, nullable=False)
    file_type = Column(String(10), default='photo')
    local_path = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<EducationalContentMedia {self.id} for EducationalContent {self.content_id}>'

class StaticContent(Base):
    __tablename__ = 'static_content'

    id = Column(Integer, primary_key=True)
    content_type = Column(String(20), nullable=False, unique=True)
    content = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<StaticContent {self.content_type}>'