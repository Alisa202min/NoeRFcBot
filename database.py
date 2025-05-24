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
            self.conn = psycopg2.connect(
                self.database_url,
                # تنظیمات اضافی برای بهبود مقاومت ارتباط
                connect_timeout=10,  # زمان برقراری اتصال - 10 ثانیه
                keepalives=1,        # فعال کردن keepalive
                keepalives_idle=30,  # بعد از 30 ثانیه idle، بسته keepalive ارسال شود
                keepalives_interval=10,  # هر 10 ثانیه بسته keepalive ارسال شود
                keepalives_count=5   # حداکثر 5 تلاش مجدد قبل از خطا
            )
            self.conn.autocommit = True
            logging.info("Database connection established successfully")
        except Exception as e:
            logging.error(f"Failed to connect to database: {str(e)}")
            raise
    
    def ensure_connection(self):
        """Ensure database connection is active, reconnect if needed"""
        if self.db_type != 'postgresql':
            return True
            
        try:
            # تلاش برای اجرای یک دستور ساده برای بررسی وضعیت اتصال
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT 1")
        except (psycopg2.OperationalError, psycopg2.InterfaceError, psycopg2.Error) as e:
            # در صورت بروز خطای ارتباطی، اتصال مجدد
            logging.warning(f"Database connection lost. Reconnecting... Error: {str(e)}")
            try:
                if hasattr(self, 'conn') and self.conn:
                    self.conn.close()
            except Exception as close_error:
                logging.warning(f"Error closing connection: {str(close_error)}")
                
            self.conn = None  # خالی کردن متغیر اتصال
                
            try:
                # سعی مجدد برای اتصال
                self.connect()
                return True
            except Exception as connect_error:
                logging.error(f"Failed to reconnect: {str(connect_error)}")
                return False
        except Exception as e:
            # سایر خطاها ممکن است نیاز به رسیدگی خاص داشته باشند
            logging.error(f"Unknown database error: {str(e)}")
            try:
                self.connect()  # تلاش مجدد برای اتصال
                return True
            except:
                return False
            
        return True
        
    def initialize(self):
        """Initialize PostgreSQL database and create necessary tables"""
        with self.conn.cursor() as cursor:
            # Create product categories table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS product_categories (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    parent_id INTEGER NULL,
                    FOREIGN KEY (parent_id) REFERENCES product_categories(id) ON DELETE CASCADE
                )
            ''')
            
            # Create service categories table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS service_categories (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    parent_id INTEGER NULL,
                    FOREIGN KEY (parent_id) REFERENCES service_categories(id) ON DELETE CASCADE
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
                        FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE CASCADE
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

    def add_category(self, name: str, parent_id: Optional[int] = None) -> int:
        """Add a new category"""
        with self.conn.cursor() as cursor:
            cursor.execute(
                'INSERT INTO product_categories (name, parent_id) VALUES (%s, %s) RETURNING id',
                (name, parent_id)
            )
            category_id = cursor.fetchone()[0]
            return category_id

    def get_product_category(self, category_id: int) -> Optional[Dict]:
        """Get a product category by ID"""
        self.ensure_connection()  # اطمینان از اتصال فعال به دیتابیس
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                'SELECT id, name, parent_id FROM product_categories WHERE id = %s',
                (category_id,)
            )
            return cursor.fetchone()
            
    def get_service_category(self, category_id: int) -> Optional[Dict]:
        """Get a service category by ID"""
        self.ensure_connection()  # اطمینان از اتصال فعال به دیتابیس
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                'SELECT id, name, parent_id FROM service_categories WHERE id = %s',
                (category_id,)
            )
            return cursor.fetchone()
            
    def get_educational_category(self, category_id: int) -> Optional[Dict]:
        """Get an educational category by ID"""
        self.ensure_connection()  # اطمینان از اتصال فعال به دیتابیس
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                'SELECT id, name, parent_id FROM educational_categories WHERE id = %s',
                (category_id,)
            )
            return cursor.fetchone()
            
    def check_product_category_exists(self, category_id: int) -> bool:
        """Check if a category exists in product_categories table"""
        self.ensure_connection()  # اطمینان از اتصال فعال به دیتابیس
        try:
            with self.conn.cursor() as cursor:
                cursor.execute('SELECT COUNT(*) FROM product_categories WHERE id = %s', (category_id,))
                count = cursor.fetchone()[0]
                return count > 0
        except Exception as e:
            logging.error(f"Error in check_product_category_exists: {str(e)}")
            return False
            
    def check_service_category_exists(self, category_id: int) -> bool:
        """Check if a category exists in service_categories table"""
        self.ensure_connection()  # اطمینان از اتصال فعال به دیتابیس
        try:
            with self.conn.cursor() as cursor:
                cursor.execute('SELECT COUNT(*) FROM service_categories WHERE id = %s', (category_id,))
                count = cursor.fetchone()[0]
                return count > 0
        except Exception as e:
            logging.error(f"Error in check_service_category_exists: {str(e)}")
            return False

    def get_product_categories_by_parent(self, parent_id: Optional[int] = None) -> List[Dict]:
        """Get product categories based on parent ID"""
        self.ensure_connection()
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            if parent_id is None:
                cursor.execute('SELECT id, name, parent_id FROM product_categories WHERE parent_id IS NULL ORDER BY name')
            else:
                cursor.execute('SELECT id, name, parent_id FROM product_categories WHERE parent_id = %s ORDER BY name', (parent_id,))
            return cursor.fetchall()

    def get_service_categories_by_parent(self, parent_id: Optional[int] = None) -> List[Dict]:
        """Get service categories based on parent ID"""
        self.ensure_connection()
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            if parent_id is None:
                cursor.execute('SELECT id, name, parent_id FROM service_categories WHERE parent_id IS NULL ORDER BY name')
            else:
                cursor.execute('SELECT id, name, parent_id FROM service_categories WHERE parent_id = %s ORDER BY name', (parent_id,))
            return cursor.fetchall()

    def get_educational_categories_by_parent(self, parent_id: Optional[int] = None) -> List[Dict]:
        """Get educational categories based on parent ID"""
        self.ensure_connection()
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            if parent_id is None:
                cursor.execute('SELECT id, name, parent_id FROM educational_categories WHERE parent_id IS NULL ORDER BY name')
            else:
                cursor.execute('SELECT id, name, parent_id FROM educational_categories WHERE parent_id = %s ORDER BY name', (parent_id,))
            return cursor.fetchall()

    def get_product_categories(self, parent_id=None) -> List[Dict]:
        """Get product categories with subcategory and product counts
        
        Args:
            parent_id: Optional parent ID to filter by. If None, returns top-level categories.
            
        Returns:
            List of product categories with counts
        """
        self.ensure_connection()  # اطمینان از اتصال فعال به دیتابیس
        
        try:
            query = 'SELECT * FROM product_categories WHERE '
            params = []
            
            if parent_id is None:
                query += 'parent_id IS NULL'
            else:
                query += 'parent_id = %s'
                params.append(parent_id)
                
            query += ' ORDER BY name'
            
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                categories = cursor.fetchall()
                
                # اضافه کردن تعداد زیرمجموعه‌ها برای هر دسته‌بندی
                for category in categories:
                    # محاسبه تعداد زیردسته‌بندی‌ها
                    cursor.execute('SELECT COUNT(*) FROM product_categories WHERE parent_id = %s', [category['id']])
                    subcategory_count = cursor.fetchone()['count']
                    
                    # محاسبه تعداد محصولات
                    cursor.execute('SELECT COUNT(*) FROM products WHERE category_id = %s', [category['id']])
                    product_count = cursor.fetchone()['count']
                    
                    # ذخیره مجموع زیردسته‌بندی‌ها و محصولات
                    category['subcategory_count'] = subcategory_count
                    category['product_count'] = product_count
                    category['total_items'] = subcategory_count + product_count
                
                return categories
        except Exception as e:
            logging.error(f"Error in get_product_categories: {e}")
            # در صورت خطا، یک بار دیگر تلاش می‌کنیم اتصال را برقرار کنیم
            try:
                self.connect()
                return self.get_product_categories(parent_id)  # تلاش مجدد
            except Exception as retry_error:
                logging.error(f"Failed retry in get_product_categories: {retry_error}")
                return []
            
    def get_service_categories(self, parent_id=None) -> List[Dict]:
        """Get service categories with subcategory and service counts
        
        Args:
            parent_id: Optional parent ID to filter by. If None, returns top-level categories.
            
        Returns:
            List of service categories with counts
        """
        self.ensure_connection()  # اطمینان از اتصال فعال به دیتابیس
        
        try:
            query = 'SELECT * FROM service_categories WHERE '
            params = []
            
            if parent_id is None:
                query += 'parent_id IS NULL'
            else:
                query += 'parent_id = %s'
                params.append(parent_id)
                
            query += ' ORDER BY name'
            
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                categories = cursor.fetchall()
                
                # اضافه کردن تعداد زیرمجموعه‌ها برای هر دسته‌بندی
                for category in categories:
                    # محاسبه تعداد زیردسته‌بندی‌ها
                    cursor.execute('SELECT COUNT(*) FROM service_categories WHERE parent_id = %s', [category['id']])
                    subcategory_count = cursor.fetchone()['count']
                    
                    # محاسبه تعداد خدمات
                    cursor.execute('SELECT COUNT(*) FROM services WHERE category_id = %s', [category['id']])
                    service_count = cursor.fetchone()['count']
                    
                    # ذخیره مجموع زیردسته‌بندی‌ها و خدمات
                    category['subcategory_count'] = subcategory_count
                    category['service_count'] = service_count
                    category['total_items'] = subcategory_count + service_count
                
                return categories
        except Exception as e:
            logging.error(f"Error in get_service_categories: {e}")
            # در صورت خطا، یک بار دیگر تلاش می‌کنیم اتصال را برقرار کنیم
            try:
                self.connect()
                return self.get_service_categories(parent_id)  # تلاش مجدد
            except Exception as retry_error:
                logging.error(f"Failed retry in get_service_categories: {retry_error}")
                return []
    
    def update_category(self, category_id: int, name: str, parent_id: Optional[int] = None, 
                       cat_type: Optional[str] = None) -> bool:
        """Update a category"""
        category = self.get_category(category_id)
        if not category:
            return False

        if parent_id is None:
            parent_id = category['parent_id']
       

        with self.conn.cursor() as cursor:
            cursor.execute(
                'UPDATE product_categories SET name = %s, parent_id = %s WHERE id = %s',
                (name, parent_id, category_id)
            )
            return cursor.rowcount > 0
        
    def delete_category(self, category_id: int) -> bool:
        """Delete a category and all its subcategories"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute('DELETE FROM product_categories WHERE id = %s', (category_id,))
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
                '''SELECT id, name, price, description, photo_url, category_id, 
                   brand, model, model_number, manufacturer, in_stock, featured, tags
                   FROM products WHERE id = %s''',
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
                '''SELECT id, name, price, description, photo_url, category_id, 
                   tags, featured, available FROM services WHERE id = %s''',
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

    def get_products(self, category_id: int) -> List[Dict]:
        """Get all products in a category
        
        Args:
            category_id: The ID of the product category
            
        Returns:
            List of products in the category
        """
        try:
            logging.info(f"Getting products for category ID: {category_id}")
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    'SELECT id, name, price, description, photo_url, category_id FROM products WHERE category_id = %s ORDER BY name',
                    (category_id,)
                )
                result = cursor.fetchall()
                logging.info(f"Found {len(result)} products in category {category_id}")
                return result
        except Exception as e:
            logging.error(f"Error in get_products: {str(e)}")
            return []
            
    def get_services(self, category_id: int) -> List[Dict]:
        """Get all services in a category
        
        Args:
            category_id: The ID of the service category
            
        Returns:
            List of services in the category
        """
        try:
            logging.info(f"Getting services for category ID: {category_id}")
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    'SELECT id, name, price, description, photo_url, category_id FROM services WHERE category_id = %s ORDER BY name',
                    (category_id,)
                )
                result = cursor.fetchall()
                logging.info(f"Found {len(result)} services in category {category_id}")
                return result
        except Exception as e:
            logging.error(f"Error in get_services: {str(e)}")
            return []

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
            The inquiry can reference either a product OR a service, not both.
        """
        with self.conn.cursor() as cursor:
            cursor.execute(
                'INSERT INTO inquiries (user_id, name, phone, description, product_id, service_id, date) VALUES (%s, %s, %s, %s, %s, %s, NOW()) RETURNING id',
                (user_id, name, phone, description, product_id, service_id)
            )
            inquiry_id = cursor.fetchone()[0]
            return inquiry_id

    def get_inquiries(self, start_date: Optional[str] = None, end_date: Optional[str] = None,
                     product_id: Optional[int] = None, service_id: Optional[int] = None) -> List[Dict]:
        """Get inquiries with optional filtering"""
        query = '''SELECT i.id, i.user_id, i.name, i.phone, i.description, 
                          i.product_id, i.service_id, i.date,
                          CASE WHEN i.service_id IS NOT NULL THEN s.name ELSE p.name END as item_name,
                          CASE WHEN i.service_id IS NOT NULL THEN 'service' ELSE 'product' END as item_type
                   FROM inquiries i 
                   LEFT JOIN products p ON i.product_id = p.id
                   LEFT JOIN services s ON i.service_id = s.id
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
            
        if service_id:
            query += 'AND i.service_id = %s '
            params.append(service_id)

        query += 'ORDER BY i.date DESC'

        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def get_inquiry(self, inquiry_id: int) -> Optional[Dict]:
        """Get an inquiry by ID"""
        query = '''SELECT i.id, i.user_id, i.name, i.phone, i.description, 
                          i.product_id, i.service_id, i.date,
                          CASE WHEN i.service_id IS NOT NULL THEN s.name ELSE p.name END as item_name,
                          CASE WHEN i.service_id IS NOT NULL THEN 'service' ELSE 'product' END as item_type
                   FROM inquiries i 
                   LEFT JOIN products p ON i.product_id = p.id
                   LEFT JOIN services s ON i.service_id = s.id
                   WHERE i.id = %s'''

        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (inquiry_id,))
            return cursor.fetchone() or None

    def get_educational_content(self, content_id: int) -> Optional[Dict]:
        """Get educational content by ID with media files"""
        # Ensure connection is active
        self.ensure_connection()
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get main content data
                cursor.execute(
                    '''SELECT ec.id, ec.title, ec.content, ec.category, 
                       ec.category_id, cat.name as category_name
                       FROM educational_content ec
                       LEFT JOIN educational_categories cat ON ec.category_id = cat.id
                       WHERE ec.id = %s''',
                    (content_id,)
                )
                content = cursor.fetchone()
                
                if not content:
                    return None
                    
                # Get media files
                cursor.execute(
                    '''SELECT id, file_id, file_type, local_path
                       FROM educational_content_media 
                       WHERE educational_content_id = %s 
                       ORDER BY file_type, id''',
                    (content_id,)
                )
                media_files = cursor.fetchall()
                
                # Add media files to content
                content['media'] = media_files
                
                return content
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            # Connection lost during query execution - reconnect and retry
            logging.warning(f"Connection error in get_educational_content: {str(e)}. Reconnecting...")
            try:
                self.conn.close()
            except:
                pass
            self.connect()
            
            # Try again with new connection
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get main content data
                cursor.execute(
                    '''SELECT ec.id, ec.title, ec.content, ec.category, 
                       ec.category_id, cat.name as category_name
                       FROM educational_content ec
                       LEFT JOIN educational_categories cat ON ec.category_id = cat.id
                       WHERE ec.id = %s''',
                    (content_id,)
                )
                content = cursor.fetchone()
                
                if not content:
                    return None
                    
                # Get media files
                cursor.execute(
                    '''SELECT id, file_id, file_type, local_path
                       FROM educational_content_media 
                       WHERE educational_content_id = %s 
                       ORDER BY file_type, id''',
                    (content_id,)
                )
                media_files = cursor.fetchall()
                
                # Add media files to content
                content['media'] = media_files
                
                return content

    def get_all_educational_content(self, category: Optional[str] = None, category_id: Optional[int] = None) -> List[Dict]:
        """
        Get all educational content with optional category filter
        
        Args:
            category (str, optional): Filter by legacy category field
            category_id (int, optional): Filter by new category_id field
            
        Returns:
            List of educational content with media count
        """
        query = '''
            SELECT ec.id, ec.title, ec.content, ec.category,
                   ec.category_id, cat.name as category_name,
                   (SELECT COUNT(*) FROM educational_content_media WHERE educational_content_id = ec.id) as media_count
            FROM educational_content ec
            LEFT JOIN educational_categories cat ON ec.category_id = cat.id
        '''
        
        params = []
        where_clauses = []

        if category:
            where_clauses.append('ec.category = %s')
            params.append(category)
            
        if category_id:
            where_clauses.append('ec.category_id = %s')
            params.append(category_id)
            
        if where_clauses:
            query += ' WHERE ' + ' AND '.join(where_clauses)

        query += ' ORDER BY ec.category, ec.title'

        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            contents = cursor.fetchall()
            
            # Optional: For each content item that has media, we could fetch the actual media files
            # This is commented out as it might be too much data to fetch at once
            # for content in contents:
            #     if content['media_count'] > 0:
            #         cursor.execute(
            #             'SELECT id, file_id, file_type FROM educational_content_media WHERE educational_content_id = %s ORDER BY file_type, id',
            #             (content['id'],)
            #         )
            #         content['media'] = cursor.fetchall()
            #     else:
            #         content['media'] = []
                    
            return contents

    def get_educational_categories(self) -> List[Dict]:
        """
        Get all educational categories with hierarchical structure
        
        Returns:
            List of category objects with id, name, parent_id
        """
        # Ensure connection is active
        self.ensure_connection()
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get all categories with their parent_id
                cursor.execute('''
                    SELECT c.id, c.name, c.parent_id, p.name as parent_name,
                        (SELECT COUNT(*) FROM educational_content WHERE category_id = c.id) as content_count,
                        (SELECT COUNT(*) FROM educational_categories WHERE parent_id = c.id) as children_count
                    FROM educational_categories c
                    LEFT JOIN educational_categories p ON c.parent_id = p.id
                    ORDER BY c.parent_id NULLS FIRST, c.name
                ''')
                return cursor.fetchall()
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            # Connection lost during query execution - reconnect and retry
            logging.warning(f"Connection error in get_educational_categories: {str(e)}. Reconnecting...")
            try:
                self.conn.close()
            except:
                pass
            self.connect()
            
            # Try again with new connection
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute('''
                    SELECT c.id, c.name, c.parent_id, p.name as parent_name,
                        (SELECT COUNT(*) FROM educational_content WHERE category_id = c.id) as content_count,
                        (SELECT COUNT(*) FROM educational_categories WHERE parent_id = c.id) as children_count
                    FROM educational_categories c
                    LEFT JOIN educational_categories p ON c.parent_id = p.id
                    ORDER BY c.parent_id NULLS FIRST, c.name
                ''')
                return cursor.fetchall()
            
    def get_educational_category_by_id(self, category_id: int) -> Optional[Dict]:
        """Get educational category by ID"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute('''
                SELECT c.id, c.name, c.parent_id, p.name as parent_name,
                       (SELECT COUNT(*) FROM educational_content WHERE category_id = c.id) as content_count
                FROM educational_categories c
                LEFT JOIN educational_categories p ON c.parent_id = p.id
                WHERE c.id = %s
            ''', (category_id,))
            return cursor.fetchone()
            
    def get_educational_subcategories(self, parent_id: int) -> List[Dict]:
        """Get subcategories for a parent category"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute('''
                SELECT c.id, c.name, c.parent_id,
                       (SELECT COUNT(*) FROM educational_content WHERE category_id = c.id) as content_count,
                       (SELECT COUNT(*) FROM educational_categories WHERE parent_id = c.id) as children_count
                FROM educational_categories c
                WHERE c.parent_id = %s
                ORDER BY c.name
            ''', (parent_id,))
            return cursor.fetchall()
            
    def get_legacy_educational_categories(self) -> List[str]:
        """Get all unique educational content categories from legacy category field"""
        with self.conn.cursor() as cursor:
            cursor.execute(
                'SELECT DISTINCT category FROM educational_content ORDER BY category'
            )
            rows = cursor.fetchall()
            return [row[0] for row in rows]

    def add_educational_content(self, title: str, content: str, category: str, 
                                category_id: Optional[int] = None, media_files: Optional[List[Dict]] = None) -> int:
        """
        Add new educational content with optional category_id and media files
        
        Args:
            title: Content title
            content: Content body text
            category: Legacy category field (for backwards compatibility)
            category_id: New hierarchical category ID (optional)
            media_files: List of media files in format [{'file_id': '...', 'file_type': 'photo'}, ...] (optional)
            
        Returns:
            ID of the newly created content
        """
        with self.conn.cursor() as cursor:
            # Insert main content record
            cursor.execute(
                '''INSERT INTO educational_content 
                   (title, content, category, category_id) 
                   VALUES (%s, %s, %s, %s) RETURNING id''',
                (title, content, category, category_id)
            )
            content_id = cursor.fetchone()[0]
            
            # If media files provided, insert them
            if media_files:
                for media in media_files:
                    file_id = media.get('file_id')
                    file_type = media.get('file_type', 'photo')
                    
                    if file_id:
                        cursor.execute(
                            '''INSERT INTO educational_content_media 
                               (educational_content_id, file_id, file_type) 
                               VALUES (%s, %s, %s)''',
                            (content_id, file_id, file_type)
                        )
            
            return content_id

    def update_educational_content(self, content_id: int, title: Optional[str] = None, 
                                 content: Optional[str] = None, category: Optional[str] = None,
                                 category_id: Optional[int] = None,
                                 media_files: Optional[List[Dict]] = None, 
                                 replace_media: bool = False) -> bool:
        """
        Update educational content with optional media management
        
        Args:
            content_id: ID of content to update
            title: New title (optional)
            content: New content body (optional)
            category: New legacy category (optional)
            category_id: New category ID in hierarchical structure (optional)
            media_files: List of media files to add (optional)
            replace_media: If True, will delete existing media files before adding new ones
            
        Returns:
            True if update was successful, False otherwise
        """
        edu_content = self.get_educational_content(content_id)
        if not edu_content:
            return False

        # Prepare values for fields that may be updated
        new_title = title if title is not None else edu_content['title']
        new_content = content if content is not None else edu_content['content']
        new_category = category if category is not None else edu_content['category']
        # We don't update category_id if it's None to avoid overwriting existing value
        new_category_id = category_id if category_id is not None else edu_content.get('category_id')

        with self.conn.cursor() as cursor:
            # Update main content record
            cursor.execute(
                '''UPDATE educational_content 
                   SET title = %s, content = %s, category = %s, category_id = %s
                   WHERE id = %s''',
                (new_title, new_content, new_category, new_category_id, content_id)
            )
            
            # Media management
            if replace_media and media_files:
                # Delete existing media
                cursor.execute(
                    'DELETE FROM educational_content_media WHERE educational_content_id = %s',
                    (content_id,)
                )
            
            # Add new media files if provided
            if media_files:
                for media in media_files:
                    file_id = media.get('file_id')
                    file_type = media.get('file_type', 'photo')
                    
                    if file_id:
                        cursor.execute(
                            '''INSERT INTO educational_content_media 
                               (educational_content_id, file_id, file_type) 
                               VALUES (%s, %s, %s)''',
                            (content_id, file_id, file_type)
                        )
            return cursor.rowcount > 0

    def delete_educational_content(self, content_id: int) -> bool:
        """Delete educational content and its media files"""
        try:
            with self.conn.cursor() as cursor:
                # Media files will be automatically deleted due to ON DELETE CASCADE constraint
                cursor.execute('DELETE FROM educational_content WHERE id = %s', (content_id,))
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error deleting educational content: {e}")
            return False
            
    def add_educational_category(self, name: str, parent_id: Optional[int] = None) -> int:
        """
        Add a new educational category
        
        Args:
            name: Category name
            parent_id: Parent category ID for hierarchical structure (optional)
            
        Returns:
            ID of the newly created category
        """
        try:
            with self.conn.cursor() as cursor:
                if parent_id:
                    # Verify parent exists
                    cursor.execute('SELECT id FROM educational_categories WHERE id = %s', (parent_id,))
                    if not cursor.fetchone():
                        raise ValueError(f"Parent category with ID {parent_id} does not exist")
                        
                cursor.execute(
                    'INSERT INTO educational_categories (name, parent_id) VALUES (%s, %s) RETURNING id',
                    (name, parent_id)
                )
                category_id = cursor.fetchone()[0]
                return category_id
        except Exception as e:
            logging.error(f"Error adding educational category: {e}")
            raise
            
    def update_educational_category(self, category_id: int, name: Optional[str] = None, 
                                   parent_id: Optional[int] = None) -> bool:
        """
        Update an educational category
        
        Args:
            category_id: ID of category to update
            name: New category name (optional)
            parent_id: New parent category ID (optional, None means no parent)
            
        Returns:
            True if update was successful
        """
        try:
            # Get current values
            category = self.get_educational_category_by_id(category_id)
            if not category:
                return False
                
            # Prevent creation of circular dependencies in parent-child relationship
            if parent_id and parent_id == category_id:
                raise ValueError("Category cannot be its own parent")
                
            # Check if making this update would create a circular dependency
            if parent_id:
                # Check if the proposed parent is actually a child of this category
                def is_child_of(check_id, target_id):
                    """Recursively check if check_id is a child of target_id"""
                    with self.conn.cursor() as cursor:
                        cursor.execute('SELECT id FROM educational_categories WHERE parent_id = %s', (target_id,))
                        for child in cursor.fetchall():
                            child_id = child[0]
                            if child_id == check_id or is_child_of(check_id, child_id):
                                return True
                    return False
                    
                if is_child_of(parent_id, category_id):
                    raise ValueError("This would create a circular dependency in the category hierarchy")
                
            # Prepare values
            new_name = name if name is not None else category['name']
            # Special handling for parent_id - None is a valid value meaning "no parent"
            update_parent = parent_id != category['parent_id']
            
            with self.conn.cursor() as cursor:
                if update_parent:
                    cursor.execute(
                        'UPDATE educational_categories SET name = %s, parent_id = %s WHERE id = %s',
                        (new_name, parent_id, category_id)
                    )
                else:
                    cursor.execute(
                        'UPDATE educational_categories SET name = %s WHERE id = %s',
                        (new_name, category_id)
                    )
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error updating educational category: {e}")
            raise
            
    def delete_educational_category(self, category_id: int, reassign_children: bool = False, 
                                    reassign_parent_id: Optional[int] = None) -> bool:
        """
        Delete an educational category
        
        Args:
            category_id: ID of category to delete
            reassign_children: If True, reassign children to a new parent instead of deleting them
            reassign_parent_id: New parent ID for children (if reassign_children is True)
            
        Returns:
            True if deletion was successful
        """
        try:
            # Check if category exists
            category = self.get_educational_category_by_id(category_id)
            if not category:
                return False
                
            with self.conn.cursor() as cursor:
                # Handle children categories
                if reassign_children:
                    if reassign_parent_id and reassign_parent_id == category_id:
                        raise ValueError("Cannot reassign to the category being deleted")
                        
                    # Reassign children to new parent
                    cursor.execute(
                        'UPDATE educational_categories SET parent_id = %s WHERE parent_id = %s',
                        (reassign_parent_id, category_id)
                    )
                    
                # Update content items to remove category_id reference
                cursor.execute(
                    'UPDATE educational_content SET category_id = NULL WHERE category_id = %s',
                    (category_id,)
                )
                
                # Delete the category
                cursor.execute('DELETE FROM educational_categories WHERE id = %s', (category_id,))
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error deleting educational category: {e}")
            raise

    def get_educational_content_media(self, content_id: int) -> List[Dict]:
        """
        Get all media files for an educational content
        
        Args:
            content_id: ID of the educational content
            
        Returns:
            List of media file objects with id, file_id, file_type
        """
        # Ensure connection is active
        self.ensure_connection()
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    '''SELECT id, file_id, file_type, created_at, local_path
                       FROM educational_content_media
                       WHERE educational_content_id = %s
                       ORDER BY file_type, id''',
                    (content_id,)
                )
                return cursor.fetchall()
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            # Connection lost during query execution - reconnect and retry
            logging.warning(f"Connection error in get_educational_content_media: {str(e)}. Reconnecting...")
            try:
                self.conn.close()
            except:
                pass
            self.connect()
            
            # Try again with new connection
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    '''SELECT id, file_id, file_type, created_at, local_path
                       FROM educational_content_media
                       WHERE educational_content_id = %s
                       ORDER BY file_type, id''',
                    (content_id,)
                )
                return cursor.fetchall()
            
    def add_educational_content_media(self, content_id: int, file_id: str, file_type: str = 'photo') -> int:
        """
        Add a media file to educational content
        
        Args:
            content_id: ID of the educational content
            file_id: Telegram file_id of the media
            file_type: Type of media ('photo', 'video', etc.)
            
        Returns:
            ID of the newly created media record
        """
        try:
            # Verify content exists
            content = self.get_educational_content(content_id)
            if not content:
                raise ValueError(f"Educational content with ID {content_id} does not exist")
                
            with self.conn.cursor() as cursor:
                cursor.execute(
                    '''INSERT INTO educational_content_media 
                       (educational_content_id, file_id, file_type) 
                       VALUES (%s, %s, %s) RETURNING id''',
                    (content_id, file_id, file_type)
                )
                media_id = cursor.fetchone()[0]
                return media_id
        except Exception as e:
            logging.error(f"Error adding educational content media: {e}")
            raise
            
    def delete_educational_content_media(self, media_id: int) -> bool:
        """
        Delete a media file from educational content
        
        Args:
            media_id: ID of the media record to delete
            
        Returns:
            True if deletion was successful
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute('DELETE FROM educational_content_media WHERE id = %s', (media_id,))
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error deleting educational content media: {e}")
            raise
    
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
                        LEFT JOIN product_categories c ON p.category_id = c.id
                        UNION ALL
                        SELECT s.id, s.name, s.price, s.description, s.photo_url,
                             s.category_id, c.name as category_name, 'service' as type
                        FROM services s
                        LEFT JOIN service_categories c ON s.category_id = c.id
                        ORDER BY type, id'''
                )
                rows = [dict(row) for row in cursor.fetchall()]

                with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['id', 'name', 'price', 'description', 'photo_url', 'category_id', 'category_name', 'type']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    for row in rows:
                        writer.writerow(row)

            elif entity_type == 'product_categories':
                cursor = self.conn.execute(
                    '''SELECT c.id, c.name, c.parent_id, 'product' as cat_type, p.name as parent_name
                       FROM product_categories c
                       LEFT JOIN product_categories p ON c.parent_id = p.id
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
                                categories = self.get_product_categories_by_parent()
                                found = False
                                for cat in categories:
                                    if cat['name'] == category_name:
                                        category_id = cat['id']
                                        found = True
                                        break

                                if not found:
                                    category_id = self.add_category(category_name, None)

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
                                parent_id=None
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
                                category=row['category']
                            )
                            success_count += 1
                        except Exception as e:
                            logging.error(f"Error importing educational content: {e}")
                            error_count += 1

            return (success_count, error_count)
        except Exception as e:
            logging.error(f"Error importing from CSV: {e}")
            return (success_count, error_count)