import os
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime
import csv
from sqlalchemy import create_engine, text, or_, and_, func, case
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import OperationalError
from app import db
from models import (ProductCategory, ServiceCategory, 
EducationalCategory,Product, Service, ProductMedia, ServiceMedia, Inquiry, EducationalContent, EducationalContentMedia, StaticContent)
from configuration import config
class Database:
    """Database abstraction layer for PostgreSQL using SQLAlchemy"""

    def __init__(self):
        """Initialize the PostgreSQL database using DATABASE_URL from environment"""
        
        self.db_type = config.get('DB_TYPE', 'postgresql').lower()
        self.database_url = os.environ.get('DATABASE_URL')
        self.test_mode = os.environ.get('TEST_MODE', 'False').lower() == 'true'

        if self.db_type == 'postgresql':
            if not self.database_url:
                raise Exception("DATABASE_URL environment variable is not set")

            # Modify database URL for test mode
            if self.test_mode:
                logging.info("TEST MODE: Using test database")
                if 'dbname=' in self.database_url:
                    self.database_url = self.database_url.replace('dbname=', 'dbname=test_')
                else:
                    logging.warning("TEST MODE: Could not modify database URL for test. Using main database.")

            # Create SQLAlchemy engine
            self.engine = create_engine(
                self.database_url,
                connect_args={
                    'connect_timeout': 10,
                    'keepalives': 1,
                    'keepalives_idle': 30,
                    'keepalives_interval': 10,
                    'keepalives_count': 5
                },
                pool_pre_ping=True  # Automatically check connection health
            )

            # Create session factory
            self.Session = scoped_session(sessionmaker(bind=self.engine, autocommit=False, autoflush=False))
            logging.info("Database connection established successfully")

    def initialize(self):
        """Initialize database and create necessary tables"""
        
        try:
            db.create_all()

            # Initialize static content if not exists
            session = self.Session()
            try:
                if not session.query(StaticContent).filter_by(content_type='contact').first():
                    session.add(StaticContent(content_type='contact', content=config.get('CONTACT_DEFAULT', 'contact us.')))
                if not session.query(StaticContent).filter_by(content_type='about').first():
                    session.add(
                        StaticContent(content_type='about',content=config.get('ABOUT_DEFAULT', 'about us.')))
                session.commit()
            except Exception as e:
                session.rollback()
                logging.error(f"Error initializing static content: {str(e)}")
                raise
            finally:
                session.close()
        except Exception as e:
            logging.error(f"Error initializing database: {str(e)}")
            raise

    def add_product_category(self, name: str, parent_id: Optional[int] = None) -> int:
        """Add a new product category"""
        session = self.Session()
        try:
            category = ProductCategory(name=name, parent_id=parent_id)
            session.add(category)
            session.commit()
            return category.id
        except Exception as e:
            session.rollback()
            logging.error(f"Error adding product category: {str(e)}")
            raise
        finally:
            session.close()

    def add_service_category(self, name: str, parent_id: Optional[int] = None) -> int:
        """Add a new service category"""
        session = self.Session()
        try:
            category = ServiceCategory(name=name, parent_id=parent_id)
            session.add(category)
            session.commit()
            return category.id
        except Exception as e:
            session.rollback()
            logging.error(f"Error adding service category: {str(e)}")
            raise
        finally:
            session.close()

    def get_product_category(self, category_id: int) -> Optional[Dict]:
        """Get a product category by ID"""
        session = self.Session()
        try:
            category = session.query(ProductCategory).filter_by(id=category_id).first()
            if category:
                return {
                    'id': category.id,
                    'name': category.name,
                    'parent_id': category.parent_id
                }
            return None
        except Exception as e:
            logging.error(f"Error getting product category: {str(e)}")
            return None
        finally:
            session.close()

    def get_service_category(self, category_id: int) -> Optional[Dict]:
        """Get a service category by ID"""
        session = self.Session()
        try:
            category = session.query(ServiceCategory).filter_by(id=category_id).first()
            if category:
                return {
                    'id': category.id,
                    'name': category.name,
                    'parent_id': category.parent_id
                }
            return None
        except Exception as e:
            logging.error(f"Error getting service category: {str(e)}")
            return None
        finally:
            session.close()

    def get_educational_category(self, category_id: int) -> Optional[Dict]:
        """Get an educational category by ID"""
        session = self.Session()
        try:
            category = session.query(EducationalCategory).filter_by(id=category_id).first()
            if category:
                return {
                    'id': category.id,
                    'name': category.name,
                    'parent_id': category.parent_id
                }
            return None
        except Exception as e:
            logging.error(f"Error getting educational category: {str(e)}")
            return None
        finally:
            session.close()

    def check_product_category_exists(self, category_id: int) -> bool:
        """Check if a category exists in product_categories table"""
        session = self.Session()
        try:
            return session.query(ProductCategory).filter_by(id=category_id).count() > 0
        except Exception as e:
            logging.error(f"Error in check_product_category_exists: {str(e)}")
            return False
        finally:
            session.close()

    def check_service_category_exists(self, category_id: int) -> bool:
        """Check if a category exists in service_categories table"""
        session = self.Session()
        try:
            return session.query(ServiceCategory).filter_by(id=category_id).count() > 0
        except Exception as e:
            logging.error(f"Error in check_service_category_exists: {str(e)}")
            return False
        finally:
            session.close()

    def get_product_categories_by_parent(self, parent_id: Optional[int] = None) -> List[Dict]:
        """Get product categories based on parent ID"""
        session = self.Session()
        try:
            query = session.query(ProductCategory)
            if parent_id is None:
                query = query.filter(ProductCategory.parent_id.is_(None))
            else:
                query = query.filter_by(parent_id=parent_id)
            categories = query.order_by(ProductCategory.name).all()
            return [{'id': c.id, 'name': c.name, 'parent_id': c.parent_id} for c in categories]
        except Exception as e:
            logging.error(f"Error getting product categories by parent: {str(e)}")
            return []
        finally:
            session.close()

    def get_service_categories_by_parent(self, parent_id: Optional[int] = None) -> List[Dict]:
        """Get service categories based on parent ID"""
        session = self.Session()
        try:
            query = session.query(ServiceCategory)
            if parent_id is None:
                query = query.filter(ServiceCategory.parent_id.is_(None))
            else:
                query = query.filter_by(parent_id=parent_id)
            categories = query.order_by(ServiceCategory.name).all()
            return [{'id': c.id, 'name': c.name, 'parent_id': c.parent_id} for c in categories]
        except Exception as e:
            logging.error(f"Error getting service categories by parent: {str(e)}")
            return []
        finally:
            session.close()

    def get_educational_categories_by_parent(self, parent_id: Optional[int] = None) -> List[Dict]:
        """Get educational categories based on parent ID"""
        session = self.Session()
        try:
            query = session.query(EducationalCategory)
            if parent_id is None:
                query = query.filter(EducationalCategory.parent_id.is_(None))
            else:
                query = query.filter_by(parent_id=parent_id)
            categories = query.order_by(EducationalCategory.name).all()
            return [{'id': c.id, 'name': c.name, 'parent_id': c.parent_id} for c in categories]
        except Exception as e:
            logging.error(f"Error getting educational categories by parent: {str(e)}")
            return []
        finally:
            session.close()

    def get_educational_categories(self, parent_id=None) -> List[Dict]:
        """Get educational categories with subcategory and content counts"""
        session = self.Session()
        try:
            query = session.query(EducationalCategory)
            if parent_id is None:
                query = query.filter(EducationalCategory.parent_id.is_(None))
            else:
                query = query.filter_by(parent_id=parent_id)

            categories = query.order_by(EducationalCategory.name).all()
            result = []
            for category in categories:
                subcategory_count = session.query(EducationalCategory).filter_by(parent_id=category.id).count()
                content_count = session.query(EducationalContent).filter_by(category_id=category.id).count()
                result.append({
                    'id': category.id,
                    'name': category.name,
                    'parent_id': category.parent_id,
                    'subcategory_count': subcategory_count,
                    'content_count': content_count,
                    'total_items': subcategory_count + content_count
                })
            return result
        except Exception as e:
            logging.error(f"Error in get_educational_categories: {str(e)}")
            return []
        finally:
            session.close()

    def get_service_categories(self, parent_id=None) -> List[Dict]:
        """Get service categories with subcategory and service counts"""
        session = self.Session()
        try:
            query = session.query(ServiceCategory)
            if parent_id is None:
                query = query.filter(ServiceCategory.parent_id.is_(None))
            else:
                query = query.filter_by(parent_id=parent_id)

            categories = query.order_by(ServiceCategory.name).all()
            result = []
            for category in categories:
                subcategory_count = session.query(ServiceCategory).filter_by(parent_id=category.id).count()
                service_count = session.query(Service).filter_by(category_id=category.id).count()
                result.append({
                    'id': category.id,
                    'name': category.name,
                    'parent_id': category.parent_id,
                    'subcategory_count': subcategory_count,
                    'service_count': service_count,
                    'total_items': subcategory_count + service_count
                })
            return result
        except Exception as e:
            logging.error(f"Error in get_service_categories: {str(e)}")
            return []
        finally:
            session.close()

    def update_product_category(self, category_id: int, name: str, parent_id: Optional[int] = None) -> bool:
        """Update a product category"""
        session = self.Session()
        try:
            category = session.query(ProductCategory).filter_by(id=category_id).first()
            if not category:
                return False

            category.name = name
            if parent_id is not None:
                category.parent_id = parent_id
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logging.error(f"Error updating product category: {str(e)}")
            return False
        finally:
            session.close()

    def update_service_category(self, category_id: int, name: str, parent_id: Optional[int] = None) -> bool:
        """Update a service category"""
        session = self.Session()
        try:
            category = session.query(ServiceCategory).filter_by(id=category_id).first()
            if not category:
                return False

            category.name = name
            if parent_id is not None:
                category.parent_id = parent_id
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logging.error(f"Error updating service category: {str(e)}")
            return False
        finally:
            session.close()

    def delete_product_category(self, category_id: int) -> bool:
        """Delete a product category and all its subcategories"""
        session = self.Session()
        try:
            category = session.query(ProductCategory).filter_by(id=category_id).first()
            if not category:
                return False
            session.delete(category)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logging.error(f"Error deleting product category: {str(e)}")
            return False
        finally:
            session.close()

    def delete_service_category(self, category_id: int) -> bool:
        """Delete a service category and all its subcategories"""
        session = self.Session()
        try:
            category = session.query(ServiceCategory).filter_by(id=category_id).first()
            if not category:
                return False
            session.delete(category)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logging.error(f"Error deleting service category: {str(e)}")
            return False
        finally:
            session.close()

    def add_product(self, name: str, price: int, description: str, 
                   category_id: int,  brand: str = '', 
                   model: str = '', in_stock: bool = True, tags: str = '', featured: bool = False) -> int:
        """Add a new product"""
        session = self.Session()
        try:
            product = Product(
                name=name,
                price=price,
                description=description,
                category_id=category_id,
                brand=brand,
                model=model,
                in_stock=in_stock,
                tags=tags,
                featured=featured
            )
            session.add(product)
            session.commit()
            return product.id
        except Exception as e:
            session.rollback()
            logging.error(f"Error adding product: {str(e)}")
            raise
        finally:
            session.close()

    def add_service(self, name: str, price: int, description: str, 
                   category_id: int, 
                   featured: bool = False, tags: str = '') -> int:
        """Add a new service to the services table"""
        session = self.Session()
        try:
            service = Service(
                name=name,
                price=price,
                description=description,
                category_id=category_id,
                featured=featured,
                tags=tags
            )
            session.add(service)
            session.commit()
            return service.id
        except Exception as e:
            session.rollback()
            logging.error(f"Error adding service: {str(e)}")
            raise
        finally:
            session.close()

    def get_product(self, product_id: int) -> Optional[Dict]:
        """Get a product by ID"""
        session = self.Session()
        try:
            product = session.query(Product).filter_by(id=product_id).first()
            if product:
                return {
                    'id': product.id,
                    'name': product.name,
                    'price': product.price,
                    'description': product.description,
                    'category_id': product.category_id,
                    'brand': product.brand,
                    'model': product.model,
                    'model_number': product.model_number,
                    'manufacturer': product.manufacturer,
                    'in_stock': product.in_stock,
                    'featured': product.featured,
                    'tags': product.tags
                }
            return None
        except Exception as e:
            logging.error(f"Error getting product: {str(e)}")
            return None
        finally:
            session.close()

    def get_product_media(self, product_id: int) -> List[Dict]:
        """Get all media files for a product"""
        session = self.Session()
        try:
            media = session.query(ProductMedia).filter_by(product_id=product_id).order_by(ProductMedia.created_at).all()
            return [{
                'id': m.id,
                'product_id': m.product_id,
                'file_id': m.file_id,
                'file_type': m.file_type,
                'created_at': m.created_at
            } for m in media]
        except Exception as e:
            logging.error(f"Error getting product media: {str(e)}")
            return []
        finally:
            session.close()

    def get_media_by_id(self, media_id: int) -> Optional[Dict]:
        """Get a specific media file by ID"""
        session = self.Session()
        try:
            media = session.query(ProductMedia).filter_by(id=media_id).first()
            if media:
                return {
                    'id': media.id,
                    'product_id': media.product_id,
                    'file_id': media.file_id,
                    'file_type': media.file_type,
                    'created_at': media.created_at
                }
            return None
        except Exception as e:
            logging.error(f"Error getting media by ID: {str(e)}")
            return None
        finally:
            session.close()

    def get_product_by_media_id(self, media_id: int) -> Optional[Dict]:
        """Get product information associated with a media ID"""
        session = self.Session()
        try:
            media = session.query(ProductMedia).filter_by(id=media_id).first()
            if media and media.product:
                return {
                    'id': media.product.id,
                    'name': media.product.name,
                    'price': media.product.price,
                    'description': media.product.description,
                    'category_id': media.product.category_id
                }
            return None
        except Exception as e:
            logging.error(f"Error getting product by media ID: {str(e)}")
            return None
        finally:
            session.close()

    def get_service(self, service_id: int) -> Optional[Dict]:
        """Get a service by ID from the services table"""
        session = self.Session()
        try:
            service = session.query(Service).filter_by(id=service_id).first()
            if service:
                return {
                    'id': service.id,
                    'name': service.name,
                    'price': service.price,
                    'description': service.description,
                    'category_id': service.category_id,
                    'tags': service.tags,
                    'featured': service.featured,
                    'available': service.available
                }
            return None
        except Exception as e:
            logging.error(f"Error getting service: {str(e)}")
            return None
        finally:
            session.close()

    def get_service_media(self, service_id: int) -> List[Dict]:
        """Get all media files for a service"""
        session = self.Session()
        try:
            media = session.query(ServiceMedia).filter_by(service_id=service_id).order_by(ServiceMedia.created_at).all()
            return [{
                'id': m.id,
                'service_id': m.service_id,
                'file_id': m.file_id,
                'file_type': m.file_type,
                'created_at': m.created_at
            } for m in media]
        except Exception as e:
            logging.error(f"Error getting service media: {str(e)}")
            return []
        finally:
            session.close()

    def get_service_media_by_id(self, media_id: int) -> Optional[Dict]:
        """Get a specific service media file by its ID"""
        session = self.Session()
        try:
            media = session.query(ServiceMedia).filter_by(id=media_id).first()
            if media:
                return {
                    'id': media.id,
                    'service_id': media.service_id,
                    'file_id': media.file_id,
                    'file_type': media.file_type,
                    'created_at': media.created_at
                }
            return None
        except Exception as e:
            logging.error(f"Error getting service media by ID: {str(e)}")
            return None
        finally:
            session.close()

    def get_service_by_media_id(self, media_id: int) -> Optional[Dict]:
        """Get the service associated with a media file"""
        session = self.Session()
        try:
            media = session.query(ServiceMedia).filter_by(id=media_id).first()
            if media and media.service:
                return {
                    'id': media.service.id,
                    'name': media.service.name,
                    'price': media.service.price,
                    'description': media.service.description,
                    'category_id': media.service.category_id,
                    'tags': media.service.tags,
                    'featured': media.service.featured,
                    'available': media.service.available
                }
            return None
        except Exception as e:
            logging.error(f"Error getting service by media ID: {str(e)}")
            return None
        finally:
            session.close()

    def get_products(self, category_id: int) -> List[Dict]:
        """Get all products in a category"""
        session = self.Session()
        try:
            products = session.query(Product).filter_by(category_id=category_id).order_by(Product.name).all()
            return [{
                'id': p.id,
                'name': p.name,
                'price': p.price,
                'description': p.description,
                'category_id': p.category_id
            } for p in products]
        except Exception as e:
            logging.error(f"Error getting products: {str(e)}")
            return []
        finally:
            session.close()

    def get_services(self, category_id: int) -> List[Dict]:
        """Get all services in a category"""
        session = self.Session()
        try:
            services = session.query(Service).filter_by(category_id=category_id).order_by(Service.name).all()
            return [{
                'id': s.id,
                'name': s.name,
                'price': s.price,
                'description': s.description,
                'category_id': s.category_id
            } for s in services]
        except Exception as e:
            logging.error(f"Error getting services: {str(e)}")
            return []
        finally:
            session.close()

    def search_products(self, query: str = None, cat_type: str = None, 
                       category_id: int = None, min_price: int = None, max_price: int = None,
                       tags: str = None, brand: str = None, in_stock: bool = None, 
                       featured: bool = None, sort_by: str = 'name', sort_order: str = 'asc') -> List[Dict]:
        """Advanced search for products/services with multiple filtering options"""
        if cat_type == 'service':
            return self._search_services(query, category_id, min_price, max_price, 
                                       tags, featured, sort_by, sort_order)
        else:
            return self._search_products(query, category_id, min_price, max_price, 
                                       tags, brand, in_stock, featured, sort_by, sort_order)

    def _search_products(self, query: str = None, category_id: int = None, 
                        min_price: int = None, max_price: int = None, tags: str = None, 
                        brand: str = None, in_stock: bool = None, featured: bool = None, 
                        sort_by: str = 'name', sort_order: str = 'asc') -> List[Dict]:
        """Internal method to search products"""
        session = self.Session()
        try:
            q = session.query(Product).join(ProductCategory, Product.category_id == ProductCategory.id)
            conditions = []

            if query:
                search_term = f'%{query.lower()}%'
                conditions.append(or_(
                    func.lower(Product.name).like(search_term),
                    func.lower(Product.description).like(search_term),
                    func.lower(Product.tags).like(search_term)
                ))

            if category_id:
                conditions.append(Product.category_id == category_id)

            if min_price is not None:
                conditions.append(Product.price >= min_price)

            if max_price is not None:
                conditions.append(Product.price <= max_price)

            if tags:
                conditions.append(func.lower(Product.tags).like(f'%{tags.lower()}%'))

            if brand:
                conditions.append(Product.brand == brand)

            if in_stock is not None:
                conditions.append(Product.in_stock == in_stock)

            if featured is not None:
                conditions.append(Product.featured == featured)

            if conditions:
                q = q.filter(and_(*conditions))

            if sort_by == 'price':
                q = q.order_by(Product.price.asc() if sort_order == 'asc' else Product.price.desc())
            elif sort_by == 'newest':
                q = q.order_by(Product.created_at.desc())
            else:
                q = q.order_by(Product.name.asc() if sort_order == 'asc' else Product.name.desc())

            products = q.all()
            return [{
                'id': p.id,
                'name': p.name,
                'price': p.price,
                'description': p.description,
                'category_id': p.category_id,
                'tags': p.tags,
                'brand': p.brand,
                'model_number': p.model_number,
                'manufacturer': p.manufacturer,
                'in_stock': p.in_stock,
                'featured': p.featured,
                'created_at': p.created_at,
                'item_type': 'product'
            } for p in products]
        except Exception as e:
            logging.error(f"Error searching products: {str(e)}")
            return []
        finally:
            session.close()

    def _search_services(self, query: str = None, category_id: int = None, 
                        min_price: int = None, max_price: int = None, tags: str = None,
                        featured: bool = None, sort_by: str = 'name', sort_order: str = 'asc') -> List[Dict]:
        """Internal method to search services"""
        session = self.Session()
        try:
            q = session.query(Service).join(ServiceCategory, Service.category_id == ServiceCategory.id)
            conditions = []

            if query:
                search_term = f'%{query.lower()}%'
                conditions.append(or_(
                    func.lower(Service.name).like(search_term),
                    func.lower(Service.description).like(search_term),
                    func.lower(Service.tags).like(search_term)
                ))

            if category_id:
                conditions.append(Service.category_id == category_id)

            if min_price is not None:
                conditions.append(Service.price >= min_price)

            if max_price is not None:
                conditions.append(Service.price <= max_price)

            if tags:
                conditions.append(func.lower(Service.tags).like(f'%{tags.lower()}%'))

            if featured is not None:
                conditions.append(Service.featured == featured)

            if conditions:
                q = q.filter(and_(*conditions))

            if sort_by == 'price':
                q = q.order_by(Service.price.asc() if sort_order == 'asc' else Service.price.desc())
            elif sort_by == 'newest':
                q = q.order_by(Service.created_at.desc())
            else:
                q = q.order_by(Service.name.asc() if sort_order == 'asc' else Service.name.desc())

            services = q.all()
            return [{
                'id': s.id,
                'name': s.name,
                'price': s.price,
                'description': s.description,
                'category_id': s.category_id,
                'tags': s.tags,
                'featured': s.featured,
                'created_at': s.created_at,
                'item_type': 'service'
            } for s in services]
        except Exception as e:
            logging.error(f"Error searching services: {str(e)}")
            return []
        finally:
            session.close()

    def update_product(self, product_id: int, name: Optional[str] = None, price: Optional[int] = None,
                      description: Optional[str] = None,
                      category_id: Optional[int] = None) -> bool:
        """Update a product"""
        session = self.Session()
        try:
            product = session.query(Product).filter_by(id=product_id).first()
            if not product:
                return False

            if name is not None:
                product.name = name
            if price is not None:
                product.price = price
            if description is not None:
                product.description = description
            
            if category_id is not None:
                product.category_id = category_id

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logging.error(f"Error updating product: {str(e)}")
            return False
        finally:
            session.close()

    def add_product_media(self, product_id: int, file_id: str, file_type: str) -> int:
        """Add media (photo/video) to a product"""
        session = self.Session()
        try:
            media = ProductMedia(product_id=product_id, file_id=file_id, file_type=file_type)
            session.add(media)
            session.commit()
            return media.id
        except Exception as e:
            session.rollback()
            logging.error(f"Error adding product media: {str(e)}")
            raise
        finally:
            session.close()

    def add_service_media(self, service_id: int, file_id: str, file_type: str) -> int:
        """Add media (photo/video) to a service"""
        session = self.Session()
        try:
            media = ServiceMedia(service_id=service_id, file_id=file_id, file_type=file_type)
            session.add(media)
            session.commit()
            return media.id
        except Exception as e:
            session.rollback()
            logging.error(f"Error adding service media: {str(e)}")
            raise
        finally:
            session.close()

    def delete_product_media(self, media_id: int) -> bool:
        """Delete a specific media file for a product"""
        session = self.Session()
        try:
            media = session.query(ProductMedia).filter_by(id=media_id).first()
            if not media:
                return False
            session.delete(media)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logging.error(f"Error deleting product media: {str(e)}")
            return False
        finally:
            session.close()

    def delete_service_media(self, media_id: int) -> bool:
        """Delete a specific media file for a service"""
        session = self.Session()
        try:
            media = session.query(ServiceMedia).filter_by(id=media_id).first()
            if not media:
                return False
            session.delete(media)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logging.error(f"Error deleting service media: {str(e)}")
            return False
        finally:
            session.close()

    def delete_product(self, product_id: int) -> bool:
        """Delete a product and all associated media"""
        session = self.Session()
        try:
            product = session.query(Product).filter_by(id=product_id).first()
            if not product:
                return False
            session.delete(product)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logging.error(f"Error deleting product: {str(e)}")
            return False
        finally:
            session.close()

    def delete_service(self, service_id: int) -> bool:
        """Delete a service and all associated media"""
        session = self.Session()
        try:
            service = session.query(Service).filter_by(id=service_id).first()
            if not service:
                return False
            session.delete(service)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logging.error(f"Error deleting service: {str(e)}")
            return False
        finally:
            session.close()

    def add_inquiry(self, user_id: int, name: str, phone: str, 
                   description: str, product_id: Optional[int] = None, service_id: Optional[int] = None) -> int:
        """Add a new price inquiry"""
        session = self.Session()
        try:
            inquiry = Inquiry(
                user_id=user_id,
                name=name,
                phone=phone,
                description=description,
                product_id=product_id,
                service_id=service_id,
                date=datetime.utcnow()
            )
            session.add(inquiry)
            session.commit()
            return inquiry.id
        except Exception as e:
            session.rollback()
            logging.error(f"Error adding inquiry: {str(e)}")
            raise
        finally:
            session.close()

    def get_inquiries(self, start_date: Optional[str] = None, end_date: Optional[str] = None,
                     product_id: Optional[int] = None, service_id: Optional[int] = None) -> List[Dict]:
        """Get inquiries with optional filtering"""
        session = self.Session()
        try:
            query = session.query(
                Inquiry.id,
                Inquiry.user_id,
                Inquiry.name,
                Inquiry.phone,
                Inquiry.description,
                Inquiry.product_id,
                Inquiry.service_id,
                Inquiry.date,
                case(
                    (Inquiry.service_id.isnot(None), Service.name),
                    else_=Product.name
                ).label('item_name'),
                case(
                    (Inquiry.service_id.isnot(None), 'service'),
                    else_='product'
                ).label('item_type')
            ).outerjoin(Product, Inquiry.product_id == Product.id
            ).outerjoin(Service, Inquiry.service_id == Service.id)

            if start_date:
                query = query.filter(Inquiry.date >= start_date)
            if end_date:
                query = query.filter(Inquiry.date <= end_date)
            if product_id:
                query = query.filter(Inquiry.product_id == product_id)
            if service_id:
                query = query.filter(Inquiry.service_id == service_id)

            inquiries = query.order_by(Inquiry.date.desc()).all()
            return [{
                'id': i.id,
                'user_id': i.user_id,
                'name': i.name,
                'phone': i.phone,
                'description': i.description,
                'product_id': i.product_id,
                'service_id': i.service_id,
                'date': i.date,
                'item_name': i.item_name,
                'item_type': i.item_type
            } for i in inquiries]
        except Exception as e:
            logging.error(f"Error getting inquiries: {str(e)}")
            return []
        finally:
            session.close()

    def get_inquiry(self, inquiry_id: int) -> Optional[Dict]:
        """Get an inquiry by ID"""
        session = self.Session()
        try:
            inquiry = session.query(
                Inquiry.id,
                Inquiry.user_id,
                Inquiry.name,
                Inquiry.phone,
                Inquiry.description,
                Inquiry.product_id,
                Inquiry.service_id,
                Inquiry.date,
                case(
                    (Inquiry.service_id.isnot(None), Service.name),
                    else_=Product.name
                ).label('item_name'),
                case(
                    (Inquiry.service_id.isnot(None), 'service'),
                    else_='product'
                ).label('item_type')
            ).outerjoin(Product, Inquiry.product_id == Product.id
            ).outerjoin(Service, Inquiry.service_id == Service.id
            ).filter(Inquiry.id == inquiry_id).first()

            if inquiry:
                return {
                    'id': inquiry.id,
                    'user_id': inquiry.user_id,
                    'name': inquiry.name,
                    'phone': inquiry.phone,
                    'description': inquiry.description,
                    'product_id': inquiry.product_id,
                    'service_id': inquiry.service_id,
                    'date': inquiry.date,
                    'item_name': inquiry.item_name,
                    'item_type': inquiry.item_type
                }
            return None
        except Exception as e:
            logging.error(f"Error getting inquiry: {str(e)}")
            return None
        finally:
            session.close()

    def get_educational_content(self, content_id: int) -> Optional[Dict]:
        """Get educational content by ID with media files"""
        session = self.Session()
        try:
            content = session.query(
                EducationalContent.id,
                EducationalContent.title,
                EducationalContent.content,
                EducationalContent.category_id,
                EducationalCategory.name.label('category_name')
            ).outerjoin(EducationalCategory, EducationalContent.category_id == EducationalCategory.id
            ).filter(EducationalContent.id == content_id).first()

            if not content:
                return None

            media_files = session.query(EducationalContentMedia).filter_by(
                content_id=content_id
            ).order_by(EducationalContentMedia.file_type, EducationalContentMedia.id).all()

            return {
                'id': content.id,
                'title': content.title,
                'content': content.content,
                'category_id': content.category_id,
                'category_name': content.category_name,
                'media': [{
                    'id': m.id,
                    'file_id': m.file_id,
                    'file_type': m.file_type,
                    'local_path': m.local_path
                } for m in media_files]
            }
        except Exception as e:
            logging.error(f"Error getting educational content: {str(e)}")
            return None
        finally:
            session.close()

    def get_all_educational_content(self, category: Optional[str] = None, category_id: Optional[int] = None) -> List[Dict]:
        """Get all educational content with optional category filter"""
        session = self.Session()
        try:
            query = session.query(
                EducationalContent.id,
                EducationalContent.title,
                EducationalContent.content,
                EducationalContent.category_id,
                EducationalCategory.name.label('category_name'),
                func.count(EducationalContentMedia.id).label('media_count')
            ).outerjoin(EducationalCategory, EducationalContent.category_id == EducationalCategory.id
            ).outerjoin(EducationalContentMedia, EducationalContentMedia.content_id == EducationalContent.id
            ).group_by(EducationalContent.id, EducationalCategory.name)

            
            if category_id:
                query = query.filter(EducationalContent.category_id == category_id)

            contents = query.order_by(EducationalContent.id.desc()).all()
            return [{
                'id': c.id,
                'title': c.title,
                'content': c.content,
                'category_id': c.category_id,
                'category_name': c.category_name,
                'media_count': c.media_count
            } for c in contents]
        except Exception as e:
            logging.error(f"Error getting all educational content: {str(e)}")
            return []
        finally:
            session.close()

 

    def get_educational_category_by_id(self, category_id: int) -> Optional[Dict]:
        """Get educational category by ID"""
        session = self.Session()
        try:
            category = session.query(
                EducationalCategory.id,
                EducationalCategory.name,
                EducationalCategory.parent_id,
                EducationalCategory.name.label('parent_name'),
                func.count(EducationalContent.id).label('content_count')
            ).outerjoin(EducationalContent, EducationalContent.category_id == EducationalCategory.id
            ).filter(EducationalCategory.id == category_id
            ).group_by(EducationalCategory.id).first()

            if category:
                return {
                    'id': category.id,
                    'name': category.name,
                    'parent_id': category.parent_id,
                    'parent_name': category.parent_name,
                    'content_count': category.content_count
                }
            return None
        except Exception as e:
            logging.error(f"Error getting educational category by ID: {str(e)}")
            return None
        finally:
            session.close()

    def get_educational_subcategories(self, parent_id: int) -> List[Dict]:
        """Get subcategories for a parent category"""
        session = self.Session()
        try:
            subcategories = session.query(
                EducationalCategory.id,
                EducationalCategory.name,
                EducationalCategory.parent_id,
                func.count(EducationalContent.id).label('content_count'),
                func.count(EducationalCategory.id).filter(EducationalCategory.parent_id == EducationalCategory.id).label('children_count')
            ).outerjoin(EducationalContent, EducationalContent.category_id == EducationalCategory.id
            ).filter(EducationalCategory.parent_id == parent_id
            ).group_by(EducationalCategory.id
            ).order_by(EducationalCategory.name).all()

            return [{
                'id': sc.id,
                'name': sc.name,
                'parent_id': sc.parent_id,
                'content_count': sc.content_count,
                'children_count': sc.children_count
            } for sc in subcategories]
        except Exception as e:
            logging.error(f"Error getting educational subcategories: {str(e)}")
            return []
        finally:
            session.close()

    def get_legacy_educational_categories(self) -> List[str]:
        """Get all unique educational content categories from legacy category field"""
        session = self.Session()
        try:
            categories = session.query(EducationalContent.category).distinct().order_by(EducationalContent.category).all()
            return [c.category for c in categories]
        except Exception as e:
            logging.error(f"Error getting legacy educational categories: {str(e)}")
            return []
        finally:
            session.close()

    def add_educational_content(self, title: str, content: str,
                               category_id: Optional[int] = None, media_files: Optional[List[Dict]] = None) -> int:
        """Add new educational content with optional category_id and media files"""
        session = self.Session()
        try:
            edu_content = EducationalContent(
                title=title,
                content=content,
               
                category_id=category_id
            )
            session.add(edu_content)
            session.flush()

            if media_files:
                for media in media_files:
                    file_id = media.get('file_id')
                    file_type = media.get('file_type', 'photo')
                    if file_id:
                        media_record = EducationalContentMedia(
                            educational_content_id=edu_content.id,
                            file_id=file_id,
                            file_type=file_type
                        )
                        session.add(media_record)

            session.commit()
            return edu_content.id
        except Exception as e:
            session.rollback()
            logging.error(f"Error adding educational content: {str(e)}")
            raise
        finally:
            session.close()

    def update_educational_content(self, content_id: int, title: Optional[str] = None, 
                                 content: Optional[str] = None, category: Optional[str] = None,
                                 category_id: Optional[int] = None,
                                 media_files: Optional[List[Dict]] = None, 
                                 replace_media: bool = False) -> bool:
        """Update educational content with optional media management"""
        session = self.Session()
        try:
            edu_content = session.query(EducationalContent).filter_by(id=content_id).first()
            if not edu_content:
                return False

            if title is not None:
                edu_content.title = title
            if content is not None:
                edu_content.content = content
            
            if category_id is not None:
                edu_content.category_id = category_id

            if replace_media and media_files:
                session.query(EducationalContentMedia).filter_by(educational_content_id=content_id).delete()

            if media_files:
                for media in media_files:
                    file_id = media.get('file_id')
                    file_type = media.get('file_type', 'photo')
                    if file_id:
                        media_record = EducationalContentMedia(
                            educational_content_id=content_id,
                            file_id=file_id,
                            file_type=file_type
                        )
                        session.add(media_record)

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logging.error(f"Error updating educational content: {str(e)}")
            return False
        finally:
            session.close()

    def delete_educational_content(self, content_id: int) -> bool:
        """Delete educational content and its media files"""
        session = self.Session()
        try:
            content = session.query(EducationalContent).filter_by(id=content_id).first()
            if not content:
                return False
            session.delete(content)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logging.error(f"Error deleting educational content: {str(e)}")
            return False
        finally:
            session.close()

    def add_educational_category(self, name: str, parent_id: Optional[int] = None) -> int:
        """Add a new educational category"""
        session = self.Session()
        try:
            if parent_id:
                parent = session.query(EducationalCategory).filter_by(id=parent_id).first()
                if not parent:
                    raise ValueError(f"Parent category with ID {parent_id} does not exist")

            category = EducationalCategory(name=name, parent_id=parent_id)
            session.add(category)
            session.commit()
            return category.id
        except Exception as e:
            session.rollback()
            logging.error(f"Error adding educational category: {str(e)}")
            raise
        finally:
            session.close()

    def update_educational_category(self, category_id: int, name: Optional[str] = None, 
                                   parent_id: Optional[int] = None) -> bool:
        """Update an educational category"""
        session = self.Session()
        try:
            category = session.query(EducationalCategory).filter_by(id=category_id).first()
            if not category:
                return False

            if parent_id and parent_id == category_id:
                raise ValueError("Category cannot be its own parent")

            if parent_id:
                def is_child_of(check_id, target_id):
                    current = session.query(EducationalCategory).filter_by(id=target_id).first()
                    if not current:
                        return False
                    if current.parent_id == check_id:
                        return True
                    return is_child_of(check_id, current.parent_id) if current.parent_id else False

                if is_child_of(parent_id, category_id):
                    raise ValueError("This would create a circular dependency in the category hierarchy")

            if name is not None:
                category.name = name
            if parent_id is not None:
                category.parent_id = parent_id

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logging.error(f"Error updating educational category: {str(e)}")
            return False
        finally:
            session.close()

    def delete_educational_category(self, category_id: int, reassign_children: bool = False, 
                                   reassign_parent_id: Optional[int] = None) -> bool:
        """Delete an educational category"""
        session = self.Session()
        try:
            category = session.query(EducationalCategory).filter_by(id=category_id).first()
            if not category:
                return False

            if reassign_children:
                if reassign_parent_id and reassign_parent_id == category_id:
                    raise ValueError("Cannot reassign to the category being deleted")

                session.query(EducationalCategory).filter_by(parent_id=category_id).update(
                    {EducationalCategory.parent_id: reassign_parent_id}
                )

            session.query(EducationalContent).filter_by(category_id=category_id).update(
                {EducationalContent.category_id: None}
            )

            session.delete(category)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logging.error(f"Error deleting educational category: {str(e)}")
            return False
        finally:
            session.close()

    def get_educational_content_media(self, content_id: int) -> List[Dict]:
        """Get all media files for an educational content"""
        session = self.Session()
        try:
            media = session.query(EducationalContentMedia).filter_by(
                content_id=content_id
            ).order_by(EducationalContentMedia.file_type, EducationalContentMedia.id).all()
            return [{
                'id': m.id,
                'file_id': m.file_id,
                'file_type': m.file_type,
                'created_at': m.created_at,
                'local_path': m.local_path
            } for m in media]
        except Exception as e:
            logging.error(f"Error getting educational content media: {str(e)}")
            return []
        finally:
            session.close()

    def add_educational_content_media(self, content_id: int, file_id: str, file_type: str = 'photo') -> int:
        """Add a media file to educational content"""
        session = self.Session()
        try:
            content = session.query(EducationalContent).filter_by(id=content_id).first()
            if not content:
                raise ValueError(f"Educational content with ID {content_id} does not exist")

            media = EducationalContentMedia(
                content_id=content_id,
                file_id=file_id,
                file_type=file_type
            )
            session.add(media)
            session.commit()
            return media.id
        except Exception as e:
            session.rollback()
            logging.error(f"Error adding educational content media: {str(e)}")
            raise
        finally:
            session.close()

    def delete_educational_content_media(self, media_id: int) -> bool:
        """Delete a media file from educational content"""
        session = self.Session()
        try:
            media = session.query(EducationalContentMedia).filter_by(id=media_id).first()
            if not media:
                return False
            session.delete(media)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logging.error(f"Error deleting educational content media: {str(e)}")
            return False
        finally:
            session.close()

    def delete_inquiry(self, inquiry_id: int) -> bool:
        """Delete an inquiry"""
        session = self.Session()
        try:
            inquiry = session.query(Inquiry).filter_by(id=inquiry_id).first()
            if not inquiry:
                return False
            session.delete(inquiry)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logging.error(f"Error deleting inquiry: {str(e)}")
            return False
        finally:
            session.close()

    def get_static_content(self, content_type: str) -> str:
        """Get static content (contact/about)"""
        session = self.Session()
        try:
            content = session.query(StaticContent).filter_by(content_type=content_type).first()
            return content.content if content else (CONTACT_DEFAULT if content_type == 'contact' else ABOUT_DEFAULT)
        except Exception as e:
            logging.error(f"Error getting static content '{content_type}': {str(e)}")
            return CONTACT_DEFAULT if content_type == 'contact' else ABOUT_DEFAULT
        finally:
            session.close()

    def update_static_content(self, content_type: str, content: str) -> bool:
        """Update static content (contact/about)"""
        if content_type not in ['contact', 'about']:
            logging.warning(f"Invalid static content type: {content_type}")
            return False

        session = self.Session()
        try:
            static_content = session.query(StaticContent).filter_by(content_type=content_type).first()
            if static_content:
                static_content.content = content
            else:
                static_content = StaticContent(content_type=content_type, content=content)
                session.add(static_content)
            session.commit()
            logging.info(f"Static content '{content_type}' updated successfully")
            return True
        except Exception as e:
            session.rollback()
            logging.error(f"Error updating static content '{content_type}': {str(e)}")
            return False
        finally:
            session.close()

    def export_to_csv(self, entity_type: str, filepath: str) -> bool:
        """Export data to CSV"""
        session = self.Session()
        try:
            if entity_type == 'products':
                query = session.query(
                    Product.id,
                    Product.name,
                    Product.price,
                    Product.description,
                    Product.category_id,
                    ProductCategory.name.label('category_name'),
                    text("'product'").label('type')
                ).outerjoin(ProductCategory, Product.category_id == ProductCategory.id
                ).union_all(
                    session.query(
                        Service.id,
                        Service.name,
                        Service.price,
                        Service.description,
                        Service.category_id,
                        ServiceCategory.name.label('category_name'),
                        text("'service'").label('type')
                    ).outerjoin(ServiceCategory, Service.category_id == ServiceCategory.id)
                ).order_by('type', 'id')

                rows = [dict(row) for row in query.all()]

                with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['id', 'name', 'price', 'description',  'category_id', 'category_name', 'type']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    for row in rows:
                        writer.writerow(row)

            elif entity_type == 'product_categories':
                query = session.query(
                    ProductCategory.id,
                    ProductCategory.name,
                    ProductCategory.parent_id,
                    text("'product'").label('cat_type'),
                    ProductCategory.name.label('parent_name')
                ).outerjoin(ProductCategory, ProductCategory.parent_id == ProductCategory.id
                ).order_by(ProductCategory.id)

                rows = [dict(row) for row in query.all()]

                with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['id', 'name', 'parent_id', 'parent_name', 'cat_type']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    for row in rows:
                        writer.writerow(row)

            elif entity_type == 'inquiries':
                inquiries = self.get_inquiries()

                with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['id', 'user_id', 'name', 'phone', 'description', 'product_id', 'service_id', 'item_name', 'item_type', 'date']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    for inquiry in inquiries:
                        writer.writerow(inquiry)

            elif entity_type == 'educational':
                educational = self.get_all_educational_content()

                with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['id', 'title', 'content', 'category', 'category_id', 'category_name', 'media_count']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    for content in educational:
                        writer.writerow(content)

            return True
        except Exception as e:
            logging.error(f"Error exporting to CSV: {str(e)}")
            return False
        finally:
            session.close()

    def import_from_csv(self, entity_type: str, filepath: str) -> Tuple[int, int]:
        """Import data from CSV"""
        session = self.Session()
        success_count = 0
        error_count = 0

        try:
            with open(filepath, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                if entity_type == 'products':
                    for row in reader:
                        try:
                            category_name = row.get('category_name')
                            category_id = int(row.get('category_id', 0))

                            if not category_id and category_name:
                                categories = self.get_product_categories_by_parent()
                                found = False
                                for cat in categories:
                                    if cat['name'] == category_name:
                                        category_id = cat['id']
                                        found = True
                                        break

                                if not found:
                                    category_id = self.add_product_category(category_name, None)

                            if category_id:
                                if row.get('type') == 'service':
                                    self.add_service(
                                        name=row['name'],
                                        price=int(row['price']),
                                        description=row.get('description', ''),
                                        category_id=category_id
                                       
                                    )
                                else:
                                    self.add_product(
                                        name=row['name'],
                                        price=int(row['price']),
                                        description=row.get('description', ''),
                                        category_id=category_id
                                        
                                    )
                                success_count += 1
                            else:
                                error_count += 1
                        except Exception as e:
                            logging.error(f"Error importing product/service: {str(e)}")
                            error_count += 1

                elif entity_type == 'categories':
                    category_id_map = {}

                    for row in reader:
                        try:
                            old_id = int(row['id'])
                            new_id = self.add_product_category(
                                name=row['name'],
                                parent_id=None
                            )
                            category_id_map[old_id] = new_id
                            success_count += 1
                        except Exception as e:
                            logging.error(f"Error importing category: {str(e)}")
                            error_count += 1

                    csvfile.seek(0)
                    next(reader)
                    for row in reader:
                        try:
                            old_id = int(row['id'])
                            parent_id = row.get('parent_id')

                            if parent_id and parent_id != 'None' and int(parent_id) in category_id_map:
                                new_id = category_id_map[old_id]
                                new_parent_id = category_id_map[int(parent_id)]

                                self.update_product_category(
                                    category_id=new_id,
                                    name=row['name'],
                                    parent_id=new_parent_id
                                )
                        except Exception as e:
                            logging.error(f"Error updating category parent: {str(e)}")

                elif entity_type == 'educational':
                    for row in reader:
                        try:
                            self.add_educational_content(
                                title=row['title'],
                                content=row['content'],
                                category=row['category']
                            )
                            success_count += 1
                        except Exception as e:
                            logging.error(f"Error importing educational content: {str(e)}")
                            error_count += 1

                session.commit()
                return (success_count, error_count)
        except Exception as e:
            session.rollback()
            logging.error(f"Error importing from CSV: {str(e)}")
            return (success_count, error_count)
        finally:
            session.close()

    def unified_search(self, search_query: str, max_results: int = 30) -> Dict[str, List[Dict]]:
        """Unified search across products, services, and educational content"""
        if not search_query or len(search_query.strip()) < 3:
            return {'products': [], 'services': [], 'educational': []}

        session = self.Session()
        query = search_query.strip().lower()
        results = {'products': [], 'services': [], 'educational': []}
        total_count = 0

        try:
            # Search Products
            if total_count < max_results:
                q = session.query(
                    Product.id,
                    Product.name,
                    Product.price,
                    Product.description,                  
                    Product.category_id,
                    Product.tags,
                    Product.brand,
                    Product.model_number,
                    Product.manufacturer,
                    Product.in_stock,
                    Product.featured,
                    ProductCategory.name.label('category_name')
                ).join(ProductCategory, Product.category_id == ProductCategory.id)

                search_pattern = f'%{query}%'
                q = q.filter(or_(
                    func.lower(Product.name).like(search_pattern),
                    func.lower(Product.description).like(search_pattern),
                    func.lower(Product.tags).like(search_pattern),
                    func.lower(Product.brand).like(search_pattern),
                    func.lower(ProductCategory.name).like(search_pattern)
                ))

                products = q.order_by(Product.featured.desc(), Product.name.asc()).limit(max_results).all()
                results['products'] = [{
                    'id': p.id,
                    'name': p.name,
                    'price': p.price,
                    'description': p.description,
                    'category_id': p.category_id,
                    'tags': p.tags,
                    'brand': p.brand,
                    'model_number': p.model_number,
                    'manufacturer': p.manufacturer,
                    'in_stock': p.in_stock,
                    'featured': p.featured,
                    'category_name': p.category_name
                } for p in products]
                total_count += len(products)

            # Search Services
            if total_count < max_results:
                remaining = max_results - total_count
                q = session.query(
                    Service.id,
                    Service.name,
                    Service.price,
                    Service.description,
                    Service.category_id,
                    Service.tags,
                    Service.featured,
                    ServiceCategory.name.label('category_name')
                ).join(ServiceCategory, Service.category_id == ServiceCategory.id)

                search_pattern = f'%{query}%'
                q = q.filter(or_(
                    func.lower(Service.name).like(search_pattern),
                    func.lower(Service.description).like(search_pattern),
                    func.lower(Service.tags).like(search_pattern),
                    func.lower(ServiceCategory.name).like(search_pattern)
                ))

                services = q.order_by(Service.featured.desc(), Service.name.asc()).limit(remaining).all()
                results['services'] = [{
                    'id': s.id,
                    'name': s.name,
                    'price': s.price,
                    'description': s.description,
                    'category_id': s.category_id,
                    'tags': s.tags,
                    'featured': s.featured,
                    'category_name': s.category_name
                } for s in services]
                total_count += len(services)

            # Search Educational Content
            if total_count < max_results:
                remaining = max_results - total_count
                q = session.query(
                    EducationalContent.id,
                    EducationalContent.title,
                    EducationalContent.content,
                    EducationalContent.category,
                    EducationalContent.category_id,
                    EducationalCategory.name.label('category_name'),
                    EducationalContent.created_at
                ).outerjoin(EducationalCategory, EducationalContent.category_id == EducationalCategory.id)

                search_pattern = f'%{query}%'
                q = q.filter(or_(
                    func.lower(EducationalContent.title).like(search_pattern),
                    func.lower(EducationalContent.content).like(search_pattern),
                    func.lower(EducationalContent.category).like(search_pattern),
                    func.lower(EducationalCategory.name).like(search_pattern)
                ))

                educational = q.order_by(EducationalContent.created_at.desc()).limit(remaining).all()
                results['educational'] = [{
                    'id': e.id,
                    'title': e.title,
                    'content': e.content,
                    'category': e.category,
                    'category_id': e.category_id,
                    'category_name': e.category_name,
                    'created_at': e.created_at
                } for e in educational]
                total_count += len(educational)

        except Exception as e:
            logging.error(f"Error in unified_search: {str(e)}")

        logging.info(f"Search '{search_query}' returned {total_count} total results: "
                    f"{len(results['products'])} products, {len(results['services'])} services, "
                    f"{len(results['educational'])} educational")

        session.close()
        return results