import os
import json
import logging
from datetime import datetime
import csv
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional, Any, Union, Tuple

from configuration import CONTACT_DEFAULT, ABOUT_DEFAULT

class Database:
    """Database abstraction layer for PostgreSQL"""

    def __init__(self):
        """Initialize the PostgreSQL database using DATABASE_URL from environment"""
        from configuration import config
        self.db_type = config.get('DB_TYPE', 'postgresql').lower()
        self.database_url = os.environ.get('DATABASE_URL')
        self.test_mode = os.environ.get('TEST_MODE', 'False').lower() == 'true'
        
        if self.db_type == 'postgresql':
            # Use PostgreSQL
            if not self.database_url:
                raise Exception("DATABASE_URL environment variable is not set")
            
            # در حالت تست، آدرس دیتابیس را تغییر می‌دهیم
            if self.test_mode:
                # استفاده از دیتابیس تست
                # برای آزمایش، از همان دیتابیس استفاده می‌کنیم، اما نام آن را تغییر می‌دهیم
                logging.info("TEST MODE: Using test database")
                if 'dbname=' in self.database_url:
                    self.database_url = self.database_url.replace('dbname=', 'dbname=test_')
                else:
                    # اگر URL به فرمت استاندارد نباشد، از دیتابیس اصلی استفاده می‌کنیم
                    logging.warning("TEST MODE: Could not modify database URL for test. Using main database.")
            
            # Connect to PostgreSQL
            self.connect()
        
    def connect(self):
        """Establish a new database connection"""
        try:
            logging.info("Establishing new database connection")
            self.conn = psycopg2.connect(self.database_url)
            self.conn.autocommit = True
            logging.info("Database connection established successfully")
        except Exception as e:
            logging.error(f"Failed to connect to database: {str(e)}")
            raise
    
    def ensure_connection(self):
        """Ensure database connection is active, reconnect if needed"""
        if self.db_type != 'postgresql':
            return
            
        try:
            # Test if connection is alive
            cur = self.conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
        except Exception as e:
            logging.warning(f"Database connection lost: {str(e)}. Attempting to reconnect...")
            self.connect()
            
        self._init_db()

    def _init_db(self):
        """Initialize PostgreSQL database and create necessary tables"""
        with self.conn.cursor() as cursor:
            # Create categories table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    parent_id INTEGER NULL,
                    cat_type TEXT NOT NULL,
                    FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE CASCADE
                )
            ''')

            # Create products table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    price INTEGER NOT NULL,
                    description TEXT,
                    photo_url TEXT,
                    category_id INTEGER NOT NULL,
                    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
                )
            ''')
            
            # Check if product_media table exists
            cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'product_media')")
            if not cursor.fetchone()[0]:
                # Create product_media table for multiple media files
                cursor.execute('''
                    CREATE TABLE product_media (
                        id SERIAL PRIMARY KEY,
                        product_id INTEGER NOT NULL,
                        file_id TEXT NOT NULL,
                        file_type TEXT NOT NULL CHECK(file_type IN ('photo', 'video')),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
                    )
                ''')
            
            # Check if service_media table exists
            cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'service_media')")
            if not cursor.fetchone()[0]:
                # Create service_media table for multiple media files
                cursor.execute('''
                    CREATE TABLE service_media (
                        id SERIAL PRIMARY KEY,
                        service_id INTEGER NOT NULL,
                        file_id TEXT NOT NULL,
                        file_type TEXT NOT NULL CHECK(file_type IN ('photo', 'video')),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (service_id) REFERENCES products(id) ON DELETE CASCADE
                    )
                ''')

            # Create inquiries table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS inquiries (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    description TEXT,
                    product_id INTEGER,
                    product_type TEXT CHECK(product_type IN ('product', 'service')),
                    date TIMESTAMP NOT NULL,
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
                )
            ''')

            # Create educational_content table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS educational_content (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT NOT NULL,
                    type TEXT NOT NULL
                )
            ''')

            # Create static_content table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS static_content (
                    id SERIAL PRIMARY KEY,
                    type TEXT NOT NULL UNIQUE,
                    content TEXT NOT NULL
                )
            ''')

            # Check if static content exists
            cursor.execute("SELECT COUNT(*) FROM static_content WHERE type = %s", ('contact',))
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO static_content (type, content) VALUES (%s, %s)",
                              ('contact', CONTACT_DEFAULT))

            cursor.execute("SELECT COUNT(*) FROM static_content WHERE type = %s", ('about',))
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO static_content (type, content) VALUES (%s, %s)",
                              ('about', ABOUT_DEFAULT))

    def add_category(self, name: str, parent_id: Optional[int] = None, cat_type: str = 'product') -> int:
        """Add a new category"""
        with self.conn.cursor() as cursor:
            cursor.execute(
                'INSERT INTO categories (name, parent_id, cat_type) VALUES (%s, %s, %s) RETURNING id',
                (name, parent_id, cat_type)
            )
            category_id = cursor.fetchone()[0]
            return category_id

    def get_category(self, category_id: int) -> Optional[Dict]:
        """Get a category by ID"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                'SELECT id, name, parent_id, cat_type FROM categories WHERE id = %s',
                (category_id,)
            )
            return cursor.fetchone() or None or None

    def get_categories(self, parent_id: Optional[int] = None, cat_type: Optional[str] = None) -> List[Dict]:
        """Get categories based on parent ID and/or type"""
        query = 'SELECT id, name, parent_id, cat_type FROM categories WHERE '
        params = []
        conditions = []

        if parent_id is None:
            conditions.append('parent_id IS NULL')
        else:
            conditions.append('parent_id = %s')
            params.append(parent_id)

        if cat_type:
            conditions.append('cat_type = %s')
            params.append(cat_type)

        if not conditions:
            query = 'SELECT id, name, parent_id, cat_type FROM categories'
        else:
            query += ' AND '.join(conditions)

        query += ' ORDER BY name'

        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def update_category(self, category_id: int, name: str, parent_id: Optional[int] = None, 
                       cat_type: Optional[str] = None) -> bool:
        """Update a category"""
        category = self.get_category(category_id)
        if not category:
            return False

        if parent_id is None:
            parent_id = category['parent_id']
        if cat_type is None:
            cat_type = category['cat_type']

        with self.conn.cursor() as cursor:
            cursor.execute(
                'UPDATE categories SET name = %s, parent_id = %s, cat_type = %s WHERE id = %s',
                (name, parent_id, cat_type, category_id)
            )
            return cursor.rowcount > 0
        
    def delete_category(self, category_id: int) -> bool:
        """Delete a category and all its subcategories"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute('DELETE FROM categories WHERE id = %s', (category_id,))
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error deleting category: {e}")
            return False

    def add_product(self, name: str, price: int, description: str, 
                   category_id: int, photo_url: Optional[str] = None, brand: str = '', 
                   model: str = '', in_stock: bool = True, tags: str = '', featured: bool = False) -> int:
        """Add a new product"""
        with self.conn.cursor() as cursor:
            cursor.execute(
                '''INSERT INTO products 
                   (name, price, description, photo_url, category_id, brand, model, in_stock, tags, featured) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id''',
                (name, price, description, photo_url, category_id, brand, model, in_stock, tags, featured)
            )
            product_id = cursor.fetchone()[0]
            return product_id

    def add_service(self, name: str, price: int, description: str, 
                   category_id: int, photo_url: Optional[str] = None, 
                   featured: bool = False, tags: str = '') -> int:
        """Add a new service to the services table"""
        with self.conn.cursor() as cursor:
            cursor.execute(
                '''INSERT INTO services 
                   (name, price, description, photo_url, category_id, featured, tags) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id''',
                (name, price, description, photo_url, category_id, featured, tags)
            )
            service_id = cursor.fetchone()[0]
            return service_id

    def get_product(self, product_id: int) -> Optional[Dict]:
        """Get a product by ID"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                'SELECT id, name, price, description, photo_url, category_id FROM products WHERE id = %s',
                (product_id,)
            )
            return cursor.fetchone() or None
            
    def get_product_media(self, product_id: int) -> List[Dict]:
        """Get all media files for a product
        
        Args:
            product_id: The ID of the product
            
        Returns:
            List of media records with file_id and file_type
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                'SELECT id, product_id, file_id, file_type, created_at FROM product_media WHERE product_id = %s ORDER BY created_at',
                (product_id,)
            )
            return cursor.fetchall()
            
    def get_media_by_id(self, media_id: int) -> Optional[Dict]:
        """Get a specific media file by ID
        
        Args:
            media_id: The ID of the media record
            
        Returns:
            Media record with file_id and file_type, or None if not found
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                'SELECT id, product_id, file_id, file_type, created_at FROM product_media WHERE id = %s',
                (media_id,)
            )
            return cursor.fetchone() or None or None
            
    def get_product_by_media_id(self, media_id: int) -> Optional[Dict]:
        """Get product information associated with a media ID
        
        Args:
            media_id: The ID of the media record
            
        Returns:
            Product record, or None if not found
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                '''
                SELECT p.id, p.name, p.price, p.description, p.photo_url, p.category_id 
                FROM products p
                JOIN product_media pm ON p.id = pm.product_id
                WHERE pm.id = %s
                ''',
                (media_id,)
            )
            return cursor.fetchone() or None or None

    def get_service(self, service_id: int) -> Optional[Dict]:
        """Get a service by ID from the services table"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                'SELECT id, name, price, description, photo_url, category_id, tags, featured FROM services WHERE id = %s',
                (service_id,)
            )
            return cursor.fetchone() or None
        
    def get_service_media(self, service_id: int) -> List[Dict]:
        """Get all media files for a service
        
        Args:
            service_id: The ID of the service
            
        Returns:
            List of media records with file_id and file_type
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                'SELECT id, service_id, file_id, file_type, created_at FROM service_media WHERE service_id = %s ORDER BY created_at',
                (service_id,)
            )
            return cursor.fetchall()
            
    def get_service_media_by_id(self, media_id: int) -> Optional[Dict]:
        """Get a specific service media file by its ID
        
        Args:
            media_id: The ID of the media file
            
        Returns:
            Media record with file_id and file_type or None if not found
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                'SELECT id, service_id, file_id, file_type, created_at FROM service_media WHERE id = %s',
                (media_id,)
            )
            return cursor.fetchone() or None or None
            
    def get_service_by_media_id(self, media_id: int) -> Optional[Dict]:
        """Get the service associated with a media file
        
        Args:
            media_id: The ID of the media file
            
        Returns:
            Service record or None if not found
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                '''SELECT s.* FROM services s
                   JOIN service_media sm ON s.id = sm.service_id
                   WHERE sm.id = %s''',
                (media_id,)
            )
            return cursor.fetchone() or None or None

    def get_products_by_category(self, category_id: int, cat_type: Optional[str] = None) -> List[Dict]:
        """Get all products/services in a category
        
        Args:
            category_id: The ID of the category
            cat_type: Optional type filter ('product' or 'service')
            
        Returns:
            List of products/services in the category
        """
        category = self.get_category(category_id)
        if not category:
            return []

        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            if cat_type == 'product':
                cursor.execute(
                    'SELECT id, name, price, description, photo_url, category_id FROM products WHERE category_id = %s ORDER BY name',
                    (category_id,)
                )
                return cursor.fetchall()
            elif cat_type == 'service':
                cursor.execute(
                    'SELECT id, name, price, description, photo_url, category_id FROM services WHERE category_id = %s ORDER BY name',
                    (category_id,)
                )
                return cursor.fetchall()
            else:
                # If no specific type is requested, fetch both products and services
                cursor.execute(
                    'SELECT id, name, price, description, photo_url, category_id, \'product\' as item_type FROM products WHERE category_id = %s ' 
                    'UNION ALL '
                    'SELECT id, name, price, description, photo_url, category_id, \'service\' as item_type FROM services WHERE category_id = %s '
                    'ORDER BY name',
                    (category_id, category_id)
                )
                return cursor.fetchall()

    def search_products(self, query: str = None, cat_type: str = None, 
                    category_id: int = None, min_price: int = None, max_price: int = None,
                    tags: str = None, brand: str = None, in_stock: bool = None, 
                    featured: bool = None, sort_by: str = 'name', sort_order: str = 'asc') -> List[Dict]:
        """
        Advanced search for products/services with multiple filtering options
        
        Args:
            query: Search text for name, description, and tags
            cat_type: 'product' or 'service'
            category_id: Category ID to filter by
            min_price: Minimum price
            max_price: Maximum price
            tags: Tag to search for (will check if exists in tags field)
            brand: Brand to filter by
            in_stock: Filter by in_stock status
            featured: Filter by featured status
            sort_by: Field to sort by (name, price, created_at)
            sort_order: Sort direction (asc, desc)
            
        Returns:
            List of matching products/services
        """
        # Determine which table to search based on cat_type
        if cat_type == 'service':
            return self._search_services(query, category_id, min_price, max_price, 
                                       tags, featured, sort_by, sort_order)
        else:
            # Default to searching products if cat_type is None or 'product'
            return self._search_products(query, category_id, min_price, max_price, 
                                       tags, brand, in_stock, featured, sort_by, sort_order)
            
    def _search_products(self, query: str = None, category_id: int = None, 
                        min_price: int = None, max_price: int = None, tags: str = None, 
                        brand: str = None, in_stock: bool = None, featured: bool = None, 
                        sort_by: str = 'name', sort_order: str = 'asc') -> List[Dict]:
        """Internal method to search products"""
        conditions = []
        params = []
        
        # Build the query conditions
        if query:
            conditions.append("(LOWER(p.name) LIKE %s OR LOWER(p.description) LIKE %s OR LOWER(p.tags) LIKE %s)")
            search_term = f'%{query.lower()}%'
            params.extend([search_term, search_term, search_term])
            
        if category_id:
            conditions.append("p.category_id = %s")
            params.append(category_id)
            
        if min_price is not None:
            conditions.append("p.price >= %s")
            params.append(min_price)
            
        if max_price is not None:
            conditions.append("p.price <= %s")
            params.append(max_price)
            
        if tags:
            conditions.append("LOWER(p.tags) LIKE %s")
            params.append(f'%{tags.lower()}%')
            
        if brand:
            conditions.append("p.brand = %s")
            params.append(brand)
            
        if in_stock is not None:
            conditions.append("p.in_stock = %s")
            params.append(in_stock)
            
        if featured is not None:
            conditions.append("p.featured = %s")
            params.append(featured)
            
        # Combine all conditions
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # Determine sort order
        order_clause = ""
        if sort_by == 'price':
            order_clause = f"p.price {sort_order}"
        elif sort_by == 'newest':
            order_clause = f"p.created_at DESC"
        else:  # Default to name
            order_clause = f"p.name {sort_order}"
            
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = f"""
                    SELECT p.id, p.name, p.price, p.description, p.photo_url, p.category_id,
                           p.tags, p.brand, p.model_number, p.manufacturer,
                           p.in_stock, p.featured, p.created_at, 'product' as item_type
                    FROM products p
                    WHERE {where_clause}
                    ORDER BY {order_clause}
                """
                cursor.execute(query, tuple(params))
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error searching products: {e}")
            return []
            
    def _search_services(self, query: str = None, category_id: int = None, 
                        min_price: int = None, max_price: int = None, tags: str = None,
                        featured: bool = None, sort_by: str = 'name', sort_order: str = 'asc') -> List[Dict]:
        """Internal method to search services"""
        conditions = []
        params = []
        
        # Build the query conditions
        if query:
            conditions.append("(LOWER(s.name) LIKE %s OR LOWER(s.description) LIKE %s OR LOWER(s.tags) LIKE %s)")
            search_term = f'%{query.lower()}%'
            params.extend([search_term, search_term, search_term])
            
        if category_id:
            conditions.append("s.category_id = %s")
            params.append(category_id)
            
        if min_price is not None:
            conditions.append("s.price >= %s")
            params.append(min_price)
            
        if max_price is not None:
            conditions.append("s.price <= %s")
            params.append(max_price)
            
        if tags:
            conditions.append("LOWER(s.tags) LIKE %s")
            params.append(f'%{tags.lower()}%')
            
        if featured is not None:
            conditions.append("s.featured = %s")
            params.append(featured)
            
        # Combine all conditions
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # Determine sort order
        order_clause = ""
        if sort_by == 'price':
            order_clause = f"s.price {sort_order}"
        elif sort_by == 'newest':
            order_clause = f"s.created_at DESC"
        else:  # Default to name
            order_clause = f"s.name {sort_order}"
            
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = f"""
                    SELECT s.id, s.name, s.price, s.description, s.photo_url, s.category_id,
                           s.tags, s.featured, s.created_at, 'service' as item_type
                    FROM services s
                    WHERE {where_clause}
                    ORDER BY {order_clause}
                """
                cursor.execute(query, tuple(params))
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error searching services: {e}")
            return []
        


    def update_product(self, product_id: int, name: Optional[str] = None, price: Optional[int] = None,
                      description: Optional[str] = None, photo_url: Optional[str] = None,
                      category_id: Optional[int] = None) -> bool:
        """Update a product"""
        product = self.get_product(product_id)
        if not product:
            return False

        new_name = name if name is not None else product['name']
        new_price = price if price is not None else product['price']
        new_description = description if description is not None else product['description']
        new_photo_url = photo_url if photo_url is not None else product['photo_url']
        new_category_id = category_id if category_id is not None else product['category_id']

        with self.conn.cursor() as cursor:
            cursor.execute(
                '''UPDATE products 
                   SET name = %s, price = %s, description = %s, photo_url = %s, category_id = %s 
                   WHERE id = %s''',
                (new_name, new_price, new_description, new_photo_url, new_category_id, product_id)
            )
            return cursor.rowcount > 0
            
    def add_product_media(self, product_id: int, file_id: str, file_type: str) -> int:
        """Add media (photo/video) to a product
        
        Args:
            product_id: The ID of the product
            file_id: The Telegram file_id of the media file
            file_type: The type of media (photo/video)
            
        Returns:
            The ID of the new media record
        """
        with self.conn.cursor() as cursor:
            cursor.execute(
                'INSERT INTO product_media (product_id, file_id, file_type) VALUES (%s, %s, %s) RETURNING id',
                (product_id, file_id, file_type)
            )
            media_id = cursor.fetchone()[0]
            return media_id
            
    def add_service_media(self, service_id: int, file_id: str, file_type: str) -> int:
        """Add media (photo/video) to a service
        
        Args:
            service_id: The ID of the service
            file_id: The Telegram file_id of the media file
            file_type: The type of media (photo/video)
            
        Returns:
            The ID of the new media record
        """
        with self.conn.cursor() as cursor:
            cursor.execute(
                'INSERT INTO service_media (service_id, file_id, file_type) VALUES (%s, %s, %s) RETURNING id',
                (service_id, file_id, file_type)
            )
            media_id = cursor.fetchone()[0]
            return media_id

    def delete_product_media(self, media_id: int) -> bool:
        """Delete a specific media file for a product
        
        Args:
            media_id: The ID of the media record to delete
            
        Returns:
            True if successfully deleted, False otherwise
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute('DELETE FROM product_media WHERE id = %s', (media_id,))
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error deleting product media: {e}")
            return False
            
    def delete_service_media(self, media_id: int) -> bool:
        """Delete a specific media file for a service
        
        Args:
            media_id: The ID of the media record to delete
            
        Returns:
            True if successfully deleted, False otherwise
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute('DELETE FROM service_media WHERE id = %s', (media_id,))
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error deleting service media: {e}")
            return False
            
    def delete_product(self, product_id: int) -> bool:
        """Delete a product and all associated media"""
        try:
            with self.conn.cursor() as cursor:
                # First delete all media files associated with this product
                cursor.execute('DELETE FROM product_media WHERE product_id = %s', (product_id,))
                # Then delete the product itself
                cursor.execute('DELETE FROM products WHERE id = %s', (product_id,))
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error deleting product: {e}")
            return False
            
    def delete_service(self, service_id: int) -> bool:
        """Delete a service and all associated media"""
        try:
            with self.conn.cursor() as cursor:
                # First delete all media files associated with this service
                cursor.execute('DELETE FROM service_media WHERE service_id = %s', (service_id,))
                # Then delete the service itself
                cursor.execute('DELETE FROM services WHERE id = %s', (service_id,))
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error deleting service: {e}")
            return False

    def add_inquiry(self, user_id: int, name: str, phone: str, 
                   description: str, product_id: Optional[int] = None, service_id: Optional[int] = None) -> int:
        """Add a new price inquiry
        
        Args:
            user_id: The user ID making the inquiry
            name: Customer name
            phone: Customer phone number
            description: Inquiry description
            product_id: ID of the product (if this is a product inquiry)
            service_id: ID of the service (if this is a service inquiry)
            
        Note:
            For services, service_id is stored in the product_id column, with product_type='service'
        """
        # Determine the type and ID to store
        is_service = service_id is not None
        item_id = service_id if is_service else product_id
        
        with self.conn.cursor() as cursor:
            cursor.execute(
                'INSERT INTO inquiries (user_id, name, phone, description, product_id, product_type, date) VALUES (%s, %s, %s, %s, %s, %s, NOW()) RETURNING id',
                (user_id, name, phone, description, item_id, 'service' if is_service else 'product')
            )
            inquiry_id = cursor.fetchone()[0]
            return inquiry_id

    def get_inquiries(self, start_date: Optional[str] = None, end_date: Optional[str] = None,
                     product_id: Optional[int] = None, product_type: Optional[str] = None) -> List[Dict]:
        """Get inquiries with optional filtering"""
        query = '''SELECT i.id, i.user_id, i.name, i.phone, i.description, 
                          i.product_id, i.product_type, i.date,
                          CASE WHEN i.product_type = 'service' THEN s.name ELSE p.name END as product_name
                   FROM inquiries i 
                   LEFT JOIN products p ON i.product_id = p.id AND i.product_type = 'product'
                   LEFT JOIN services s ON i.product_id = s.id AND i.product_type = 'service'
                   WHERE 1=1 '''
        params = []

        if start_date:
            query += 'AND i.date >= %s '
            params.append(start_date)

        if end_date:
            query += 'AND i.date <= %s '
            params.append(end_date)

        if product_id:
            query += 'AND i.product_id = %s '
            params.append(product_id)
            
        if product_type:
            query += 'AND i.product_type = %s '
            params.append(product_type)

        query += 'ORDER BY i.date DESC'

        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def get_inquiry(self, inquiry_id: int) -> Optional[Dict]:
        """Get an inquiry by ID"""
        query = '''SELECT i.id, i.user_id, i.name, i.phone, i.description, 
                          i.product_id, i.product_type, i.date,
                          CASE WHEN i.product_type = 'service' THEN s.name ELSE p.name END as product_name
                   FROM inquiries i 
                   LEFT JOIN products p ON i.product_id = p.id AND i.product_type = 'product'
                   LEFT JOIN services s ON i.product_id = s.id AND i.product_type = 'service'
                   WHERE i.id = %s'''

        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (inquiry_id,))
            return cursor.fetchone() or None or None

    def get_educational_content(self, content_id: int) -> Optional[Dict]:
        """Get educational content by ID"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                'SELECT id, title, content, category, content_type FROM educational_content WHERE id = %s',
                (content_id,)
            )
            return cursor.fetchone() or None

    def get_all_educational_content(self, category: Optional[str] = None) -> List[Dict]:
        """Get all educational content with optional category filter"""
        query = 'SELECT id, title, content, category, content_type FROM educational_content'
        params = []

        if category:
            query += ' WHERE category = %s'
            params.append(category)

        query += ' ORDER BY category, title'

        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def get_educational_categories(self) -> List[str]:
        """Get all unique educational content categories"""
        with self.conn.cursor() as cursor:
            cursor.execute(
                'SELECT DISTINCT category FROM educational_content ORDER BY category'
            )
            rows = cursor.fetchall()
            return [row[0] for row in rows]

    def add_educational_content(self, title: str, content: str, category: str, content_type: str) -> int:
        """Add new educational content"""
        with self.conn.cursor() as cursor:
            cursor.execute(
                'INSERT INTO educational_content (title, content, category, content_type, type) VALUES (%s, %s, %s, %s, %s) RETURNING id',
                (title, content, category, content_type, content_type)
            )
            content_id = cursor.fetchone()[0]
            return content_id

    def update_educational_content(self, content_id: int, title: Optional[str] = None, 
                                 content: Optional[str] = None, category: Optional[str] = None, 
                                 content_type: Optional[str] = None) -> bool:
        """Update educational content"""
        edu_content = self.get_educational_content(content_id)
        if not edu_content:
            return False

        new_title = title if title is not None else edu_content['title']
        new_content = content if content is not None else edu_content['content']
        new_category = category if category is not None else edu_content['category']
        new_type = content_type if content_type is not None else edu_content['content_type']

        with self.conn.cursor() as cursor:
            cursor.execute(
                '''UPDATE educational_content 
                   SET title = %s, content = %s, category = %s, content_type = %s, type = %s 
                   WHERE id = %s''',
                (new_title, new_content, new_category, new_type, new_type, content_id)
            )
            return cursor.rowcount > 0

    def delete_educational_content(self, content_id: int) -> bool:
        """Delete educational content"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute('DELETE FROM educational_content WHERE id = %s', (content_id,))
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error deleting educational content: {e}")
            return False

    def delete_inquiry(self, inquiry_id: int) -> bool:
        """Delete an inquiry"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute('DELETE FROM inquiries WHERE id = %s', (inquiry_id,))
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error deleting inquiry: {e}")
            return False

    def get_static_content(self, content_type: str) -> str:
        """Get static content (contact/about)"""
        try:
            # Ensure connection is active before proceeding
            self.ensure_connection()
            
            with self.conn.cursor() as cursor:
                cursor.execute(
                    'SELECT content FROM static_content WHERE type = %s',
                    (content_type,)
                )
                row = cursor.fetchone()
                return row[0] if row else (CONTACT_DEFAULT if content_type == 'contact' else ABOUT_DEFAULT)
        except Exception as e:
            logging.error(f"Error getting static content '{content_type}': {str(e)}")
            # Return defaults if database operation fails
            return CONTACT_DEFAULT if content_type == 'contact' else ABOUT_DEFAULT

    def update_static_content(self, content_type: str, content: str) -> bool:
        """Update static content (contact/about)"""
        if content_type not in ['contact', 'about']:
            logging.warning(f"Invalid static content type: {content_type}")
            return False
            
        try:
            # Ensure connection is active before proceeding
            self.ensure_connection()
            
            with self.conn.cursor() as cursor:
                cursor.execute(
                    'UPDATE static_content SET content = %s WHERE type = %s',
                    (content, content_type)
                )
                
                if cursor.rowcount == 0:
                    # If no rows were updated, insert a new record
                    cursor.execute(
                        'INSERT INTO static_content (type, content) VALUES (%s, %s)',
                        (content_type, content)
                    )
                
                logging.info(f"Static content '{content_type}' updated successfully")
                return True
        except Exception as e:
            logging.error(f"Error updating static content '{content_type}': {str(e)}")
            return False

    def export_to_csv(self, entity_type: str, filepath: str) -> bool:
        """Export data to CSV"""
        try:
            if entity_type == 'products':
                cursor = self.conn.execute(
                    '''SELECT p.id, p.name, p.price, p.description, p.photo_url, 
                             p.category_id, c.name as category_name, 'product' as type
                        FROM products p
                        LEFT JOIN categories c ON p.category_id = c.id
                        UNION ALL
                        SELECT s.id, s.name, s.price, s.description, s.photo_url,
                             s.category_id, c.name as category_name, 'service' as type
                        FROM services s
                        LEFT JOIN categories c ON s.category_id = c.id
                        ORDER BY type, id'''
                )
                rows = [dict(row) for row in cursor.fetchall()]

                with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['id', 'name', 'price', 'description', 'photo_url', 'category_id', 'category_name', 'type']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    for row in rows:
                        writer.writerow(row)

            elif entity_type == 'categories':
                cursor = self.conn.execute(
                    '''SELECT c.id, c.name, c.parent_id, c.cat_type, p.name as parent_name
                       FROM categories c
                       LEFT JOIN categories p ON c.parent_id = p.id
                       ORDER BY c.id'''
                )
                rows = [dict(row) for row in cursor.fetchall()]

                with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['id', 'name', 'parent_id', 'parent_name', 'cat_type']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    for row in rows:
                        writer.writerow(row)

            elif entity_type == 'inquiries':
                inquiries = self.get_inquiries()

                with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['id', 'user_id', 'name', 'phone', 'description', 'product_id', 'product_type', 'product_name', 'date']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    for inquiry in inquiries:
                        writer.writerow(inquiry)

            elif entity_type == 'educational':
                educational = self.get_all_educational_content()

                with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['id', 'title', 'content', 'category', 'type']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    for content in educational:
                        writer.writerow(content)

            return True
        except Exception as e:
            logging.error(f"Error exporting to CSV: {e}")
            return False

    def import_from_csv(self, entity_type: str, filepath: str) -> Tuple[int, int]:
        """Import data from CSV"""
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
                                categories = self.get_categories()
                                found = False
                                for cat in categories:
                                    if cat['name'] == category_name:
                                        category_id = cat['id']
                                        found = True
                                        break

                                if not found:
                                    category_id = self.add_category(category_name, None, 'product')

                            if category_id:
                                self.add_product(
                                    name=row['name'],
                                    price=int(row['price']),
                                    description=row.get('description', ''),
                                    category_id=category_id,
                                    photo_url=row.get('photo_url', '')
                                )
                                success_count += 1
                            else:
                                error_count += 1
                        except Exception as e:
                            logging.error(f"Error importing product: {e}")
                            error_count += 1

                elif entity_type == 'categories':
                    category_id_map = {}

                    for row in reader:
                        try:
                            old_id = int(row['id'])
                            new_id = self.add_category(
                                name=row['name'],
                                parent_id=None,
                                cat_type=row.get('cat_type', 'product')
                            )
                            category_id_map[old_id] = new_id
                            success_count += 1
                        except Exception as e:
                            logging.error(f"Error importing category: {e}")
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

                                self.update_category(
                                    category_id=new_id,
                                    name=row['name'],
                                    parent_id=new_parent_id,
                                    cat_type=row.get('cat_type', 'product')
                                )
                        except Exception as e:
                            logging.error(f"Error updating category parent: {e}")

                elif entity_type == 'educational':
                    for row in reader:
                        try:
                            self.add_educational_content(
                                title=row['title'],
                                content=row['content'],
                                category=row['category'],
                                content_type=row['type']
                            )
                            success_count += 1
                        except Exception as e:
                            logging.error(f"Error importing educational content: {e}")
                            error_count += 1

            return (success_count, error_count)
        except Exception as e:
            logging.error(f"Error importing from CSV: {e}")
            return (success_count, error_count)