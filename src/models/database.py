"""
لایه انتزاعی دیتابیس
این ماژول رابط‌های ساده‌ای برای تعامل با دیتابیس فراهم می‌کند.
"""

import os
import psycopg2
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Database:
    """Database abstraction layer for PostgreSQL"""
    
    def __init__(self):
        """Initialize the PostgreSQL database using DATABASE_URL from environment"""
        self.conn = None
        self.cursor = None
        self._init_db()
    
    def _init_db(self):
        """Initialize PostgreSQL database and create necessary tables"""
        try:
            database_url = os.environ.get('DATABASE_URL')
            self.conn = psycopg2.connect(database_url, sslmode='prefer', 
                                         application_name='RFCBot',
                                         connect_timeout=10)
            self.conn.autocommit = True
            self.cursor = self.conn.cursor()
            logger.info("Connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def _ensure_connection(self):
        """Ensure database connection is active"""
        try:
            # Try a simple query to test connection
            self.cursor.execute("SELECT 1")
        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            # Reconnect if connection is closed
            self._init_db()
    
    # Category Methods
    
    def add_category(self, name: str, parent_id: Optional[int] = None, cat_type: str = 'product') -> int:
        """Add a new category"""
        self._ensure_connection()
        try:
            self.cursor.execute(
                """
                INSERT INTO categories (name, parent_id) 
                VALUES (%s, %s) RETURNING id
                """, 
                (name, parent_id, cat_type)
            )
            category_id = self.cursor.fetchone()[0]
            return category_id
        except Exception as e:
            logger.error(f"Error adding category: {e}")
            return 0
    
    def get_category(self, category_id: int) -> Optional[Dict]:
        """Get a category by ID"""
        self._ensure_connection()
        try:
            self.cursor.execute(
                """
                SELECT id, name, parent_id, cat_type, created_at, updated_at
                FROM categories
                WHERE id = %s
                """, 
                (category_id,)
            )
            category = self.cursor.fetchone()
            if category:
                return {
                    'id': category[0],
                    'name': category[1],
                    'parent_id': category[2],
                    'cat_type': category[3],
                    'created_at': category[4],
                    'updated_at': category[5]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting category: {e}")
            return None
    
    def get_categories(self, parent_id: Optional[int] = None) -> List[Dict]:
        """Get categories based on parent ID and/or type"""
        self._ensure_connection()
        try:
            query = """
                SELECT id, name, parent_id, cat_type, created_at, updated_at
                FROM categories
                WHERE 1=1
            """
            params = []
            
            if parent_id is not None:
                query += " AND parent_id = %s"
                params.append(parent_id)
            
            
            
            query += " ORDER BY name"
            
            self.cursor.execute(query, params)
            categories = self.cursor.fetchall()
            
            result = []
            for category in categories:
                result.append({
                    'id': category[0],
                    'name': category[1],
                    'parent_id': category[2],
                    'created_at': category[3],
                    'updated_at': category[4]
                })
            
            return result
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []
    
    # Product Methods
    
    def add_product(self, name: str, price: int, description: str, 
                   category_id: int, photo_url: Optional[str] = None, brand: str = '', 
                   model: str = '', in_stock: bool = True, tags: str = '', featured: bool = False) -> int:
        """Add a new product"""
        self._ensure_connection()
        try:
            self.cursor.execute(
                """
                INSERT INTO products 
                (name, price, description, category_id, photo_url,  brand, model, in_stock, tags, featured) 
                VALUES (%s, %s, %s,  %s, %s, %s, %s, %s, %s, %s) RETURNING id
                """, 
                (name, price, description, category_id, photo_url, 'product', 
                 brand, model, in_stock, tags, featured)
            )
            product_id = self.cursor.fetchone()[0]
            return product_id
        except Exception as e:
            logger.error(f"Error adding product: {e}")
            return 0
    
    def add_service(self, name: str, price: int, description: str, 
                   category_id: int, photo_url: Optional[str] = None, 
                   featured: bool = False, tags: str = '') -> int:
        """Add a new service - now all stored in products table with cat_type determining the type"""
        self._ensure_connection()
        try:
            self.cursor.execute(
                """
                INSERT INTO products 
                (name, price, description, category_id, photo_url,  featured, tags) 
                VALUES (%s, %s,  %s, %s, %s, %s, %s) RETURNING id
                """, 
                (name, price, description, category_id, photo_url, 'service', featured, tags)
            )
            service_id = self.cursor.fetchone()[0]
            return service_id
        except Exception as e:
            logger.error(f"Error adding service: {e}")
            return 0
    
    # ... other database methods ...
    
    def __del__(self):
        """Close database connections on delete"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()