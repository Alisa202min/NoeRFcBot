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
    last_seen = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return self.password_hash and check_password_hash(self.password_hash, password)
    
    @classmethod
    def get_or_create_telegram_user(cls, telegram_id, username=None, first_name=None, last_name=None):
        """Get an existing Telegram user or create a new one"""
        user = cls.query.filter_by(telegram_id=telegram_id).first()
        
        if not user:
            # Create a new user
            user = cls(
                username=f"telegram_{telegram_id}",
                telegram_id=telegram_id,
                telegram_username=username,
                first_name=first_name,
                last_name=last_name,
                is_admin=False
            )
            db.session.add(user)
            db.session.commit()
        elif username and (user.telegram_username != username or 
                          user.first_name != first_name or 
                          user.last_name != last_name):
            # Update user information
            user.telegram_username = username
            user.first_name = first_name
            user.last_name = last_name
            user.last_seen = datetime.utcnow()
            db.session.commit()
        
        return user


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
    # Additional fields for search/filtering
    tags = db.Column(db.String(255), nullable=True)  # Comma-separated tags
    # Product-specific fields
    brand = db.Column(db.String(100), nullable=True)
    model_number = db.Column(db.String(100), nullable=True)
    manufacturer = db.Column(db.String(100), nullable=True)
    # Service-specific fields
    provider = db.Column(db.String(100), nullable=True)
    service_code = db.Column(db.String(100), nullable=True)
    duration = db.Column(db.String(100), nullable=True)
    # Common fields
    in_stock = db.Column(db.Boolean, default=True)  # For services, this means "available"
    featured = db.Column(db.Boolean, default=False)
    
    # Relationships
    media_files = db.relationship('ProductMedia', backref='product', lazy=True, cascade="all, delete-orphan")
    inquiries = db.relationship('Inquiry', backref='product', lazy=True)
    
    def __repr__(self):
        return f'<Product {self.name}>'
        
    @classmethod
    def search(cls, query, product_type=None, category_id=None, min_price=None, max_price=None, 
               tags=None, brand=None, manufacturer=None, model_number=None, 
               provider=None, service_code=None, duration=None,
               in_stock=None, featured=None):
        """
        Advanced search method for products and services
        
        Args:
            query (str): Search text for name and description
            product_type (str): 'product' or 'service'
            category_id (int): Category ID to filter by
            min_price (int): Minimum price
            max_price (int): Maximum price
            tags (str): Comma-separated tags to search for
            brand (str): Brand name to filter by (products)
            manufacturer (str): Manufacturer to filter by (products)
            model_number (str): Model number to filter by (products)
            provider (str): Service provider to filter by (services)
            service_code (str): Service code to filter by (services)
            duration (str): Service duration to filter by (services)
            in_stock (bool): Filter by in_stock status (for services, means "available")
            featured (bool): Filter by featured status
            
        Returns:
            Query object with filters applied
        """
        search_query = cls.query
        
        # Filter by product type
        if product_type:
            search_query = search_query.filter(cls.product_type == product_type)
        
        # Text search in name and description
        if query:
            search_terms = "%" + query.lower() + "%"
            search_conditions = [
                db.func.lower(cls.name).like(search_terms),
                db.func.lower(cls.description).like(search_terms)
            ]
            
            # Include tags, brand, manufacturer in search if they exist
            if cls.tags is not None:
                search_conditions.append(db.func.lower(cls.tags).like(search_terms))
            if cls.brand is not None:
                search_conditions.append(db.func.lower(cls.brand).like(search_terms))
            if cls.manufacturer is not None:
                search_conditions.append(db.func.lower(cls.manufacturer).like(search_terms))
            if cls.model_number is not None:
                search_conditions.append(db.func.lower(cls.model_number).like(search_terms))
            if cls.provider is not None:
                search_conditions.append(db.func.lower(cls.provider).like(search_terms))
            if cls.service_code is not None:
                search_conditions.append(db.func.lower(cls.service_code).like(search_terms))
                
            search_query = search_query.filter(db.or_(*search_conditions))
        
        # Filter by category
        if category_id:
            search_query = search_query.filter(cls.category_id == category_id)
        
        # Price range filters
        if min_price is not None:
            search_query = search_query.filter(cls.price >= min_price)
        if max_price is not None:
            search_query = search_query.filter(cls.price <= max_price)
        
        # Tag filtering
        if tags:
            # For each tag, check if it exists in the comma-separated tags field
            for tag in tags.split(','):
                search_query = search_query.filter(cls.tags.like(f"%{tag.strip()}%"))
        
        # Product-specific filters
        if brand:
            search_query = search_query.filter(cls.brand == brand)
        if manufacturer:
            search_query = search_query.filter(cls.manufacturer == manufacturer)
        if model_number:
            search_query = search_query.filter(cls.model_number == model_number)
            
        # Service-specific filters
        if provider:
            search_query = search_query.filter(cls.provider == provider)
        if service_code:
            search_query = search_query.filter(cls.service_code == service_code)
        if duration:
            search_query = search_query.filter(cls.duration == duration)
        
        # Stock status (available for services)
        if in_stock is not None:
            search_query = search_query.filter(cls.in_stock == in_stock)
        
        # Featured status
        if featured is not None:
            search_query = search_query.filter(cls.featured == featured)
        
        return search_query


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
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # Required in database
    status = db.Column(db.String(20), nullable=False, default='new')  # 'new', 'in_progress', 'completed'
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
    type = db.Column(db.String(20), nullable=False, default='general')  # Column required by the database
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