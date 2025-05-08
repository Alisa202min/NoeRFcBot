import os
import json
import psycopg2
import psycopg2.extras
import logging
from datetime import datetime
import csv
from typing import Dict, List, Optional, Any, Union, Tuple

import configuration

class Database:
    """Database abstraction layer using PostgreSQL"""

    def __init__(self):
        """Initialize the PostgreSQL database using connection info from environment"""
        from configuration import config
        
        # Default to environment variable, but allow config override
        database_url = os.environ.get('DATABASE_URL', config.get('DATABASE_URL', ''))
        
        # Connect to PostgreSQL
        self.conn = psycopg2.connect(database_url)
        self.conn.autocommit = False  # Use transactions for safety
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
                    video_url TEXT,
                    file_id TEXT,
                    video_file_id TEXT,
                    category_id INTEGER NOT NULL,
                    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
                )
            ''')

            # Create services table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS services (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    price INTEGER NOT NULL,
                    description TEXT,
                    photo_url TEXT,
                    video_url TEXT,
                    file_id TEXT,
                    video_file_id TEXT,
                    category_id INTEGER NOT NULL,
                    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
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
            
            # Commit the schema changes
            self.conn.commit()

            # Insert default static content if they don't exist
            from configuration import CONTACT_DEFAULT, ABOUT_DEFAULT
            
            # Check if contact content exists
            cursor.execute("SELECT COUNT(*) FROM static_content WHERE type = %s", ('contact',))
            result = cursor.fetchone()
            if result and result[0] == 0:
                cursor.execute(
                    "INSERT INTO static_content (type, content) VALUES (%s, %s)",
                    ('contact', CONTACT_DEFAULT)
                )
                
            # Check if about content exists
            cursor.execute("SELECT COUNT(*) FROM static_content WHERE type = %s", ('about',))
            result = cursor.fetchone()
            if result and result[0] == 0:
                cursor.execute(
                    "INSERT INTO static_content (type, content) VALUES (%s, %s)",
                    ('about', ABOUT_DEFAULT)
                )
                
            # Commit the data inserts
            self.conn.commit()

    def add_category(self, name: str, parent_id: Optional[int] = None, cat_type: str = 'product') -> int:
        """Add a new category"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    'INSERT INTO categories (name, parent_id, cat_type) VALUES (%s, %s, %s) RETURNING id',
                    (name, parent_id, cat_type)
                )
                result = cursor.fetchone()
                category_id = result[0] if result else 0
                self.conn.commit()
                return category_id
        except Exception as e:
            logging.error(f"Error adding category: {e}")
            self.conn.rollback()
            return 0

    def get_category(self, category_id: int) -> Optional[Dict]:
        """Get a category by ID"""
        with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute(
                'SELECT id, name, parent_id, cat_type FROM categories WHERE id = %s',
                (category_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

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

        with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

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
            self.conn.commit()
        return True

    def delete_category(self, category_id: int) -> bool:
        """Delete a category and all its subcategories"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute('DELETE FROM categories WHERE id = %s', (category_id,))
                self.conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error deleting category: {e}")
            self.conn.rollback()
            return False

    def add_product(self, name: str, price: int, description: str, 
                   category_id: int, photo_url: Optional[str] = None, video_url: Optional[str] = None,
                   file_id: Optional[str] = None, video_file_id: Optional[str] = None) -> int:
        """Add a new product"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    '''INSERT INTO products 
                       (name, price, description, photo_url, video_url, file_id, video_file_id, category_id) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id''',
                    (name, price, description, photo_url, video_url, file_id, video_file_id, category_id)
                )
                result = cursor.fetchone()
                product_id = result[0] if result else 0
                self.conn.commit()
                return product_id
        except Exception as e:
            logging.error(f"Error adding product: {e}")
            self.conn.rollback()
            return 0

    def add_service(self, name: str, price: int, description: str, 
                   category_id: int, photo_url: Optional[str] = None, video_url: Optional[str] = None,
                   file_id: Optional[str] = None, video_file_id: Optional[str] = None) -> int:
        """Add a new service"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    '''INSERT INTO services 
                       (name, price, description, photo_url, video_url, file_id, video_file_id, category_id) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id''',
                    (name, price, description, photo_url, video_url, file_id, video_file_id, category_id)
                )
                result = cursor.fetchone()
                service_id = result[0] if result else 0
                self.conn.commit()
                return service_id
        except Exception as e:
            logging.error(f"Error adding service: {e}")
            self.conn.rollback()
            return 0

    def get_product(self, product_id: int) -> Optional[Dict]:
        """Get a product by ID"""
        with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute(
                '''SELECT id, name, price, description, photo_url, video_url, file_id, video_file_id, category_id 
                   FROM products WHERE id = %s''',
                (product_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_service(self, service_id: int) -> Optional[Dict]:
        """Get a service by ID"""
        with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute(
                '''SELECT id, name, price, description, photo_url, video_url, file_id, video_file_id, category_id 
                   FROM services WHERE id = %s''',
                (service_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_products_by_category(self, category_id: int) -> List[Dict]:
        """Get all products/services in a category"""
        category = self.get_category(category_id)
        if not category:
            return []

        with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            if category['cat_type'] == 'product':
                cursor.execute(
                    'SELECT id, name, price, description, photo_url, category_id FROM products WHERE category_id = %s ORDER BY name',
                    (category_id,)
                )
            else:
                cursor.execute(
                    'SELECT id, name, price, description, photo_url, category_id FROM services WHERE category_id = %s ORDER BY name',
                    (category_id,)
                )
            return [dict(row) for row in cursor.fetchall()]

    def search_products(self, query: str, cat_type: str = 'product') -> List[Dict]:
        """Search for products/services by name"""
        query = query.lower()
        table = 'products' if cat_type == 'product' else 'services'

        with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute(
                f'SELECT id, name, price, description, photo_url, category_id FROM {table} WHERE LOWER(name) LIKE %s ORDER BY name',
                (f'%{query}%',)
            )
            return [dict(row) for row in cursor.fetchall()]

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
            self.conn.commit()
        return True

    def delete_product(self, product_id: int) -> bool:
        """Delete a product"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute('DELETE FROM products WHERE id = %s', (product_id,))
                self.conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error deleting product: {e}")
            self.conn.rollback()
            return False

    def add_inquiry(self, user_id: int, name: str, phone: str, 
                   description: str, product_id: Optional[int] = None) -> int:
        """Add a new price inquiry"""
        try:
            date = datetime.now().isoformat()
            with self.conn.cursor() as cursor:
                cursor.execute(
                    'INSERT INTO inquiries (user_id, name, phone, description, product_id, date) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id',
                    (user_id, name, phone, description, product_id, date)
                )
                result = cursor.fetchone()
                inquiry_id = result[0] if result else 0
                self.conn.commit()
                return inquiry_id
        except Exception as e:
            logging.error(f"Error adding inquiry: {e}")
            self.conn.rollback()
            return 0

    def get_inquiries(self, start_date: Optional[str] = None, end_date: Optional[str] = None,
                     product_id: Optional[int] = None) -> List[Dict]:
        """Get inquiries with optional filtering"""
        query = '''SELECT i.id, i.user_id, i.name, i.phone, i.description, 
                          i.product_id, i.date,
                          COALESCE(p.name, s.name) as product_name
                   FROM inquiries i 
                   LEFT JOIN products p ON i.product_id = p.id
                   LEFT JOIN services s ON i.product_id = s.id
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

        query += 'ORDER BY i.date DESC'

        with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_inquiry(self, inquiry_id: int) -> Optional[Dict]:
        """Get an inquiry by ID"""
        query = '''SELECT i.id, i.user_id, i.name, i.phone, i.description, 
                          i.product_id, i.date, 
                          COALESCE(p.name, s.name) as product_name
                   FROM inquiries i 
                   LEFT JOIN products p ON i.product_id = p.id 
                   LEFT JOIN services s ON i.product_id = s.id
                   WHERE i.id = %s'''

        with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute(query, (inquiry_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
            
    def delete_inquiry(self, inquiry_id: int) -> bool:
        """Delete an inquiry"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute('DELETE FROM inquiries WHERE id = %s', (inquiry_id,))
                self.conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error deleting inquiry: {e}")
            self.conn.rollback()
            return False

    def get_educational_content(self, content_id: int) -> Optional[Dict]:
        """Get educational content by ID"""
        with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute(
                'SELECT id, title, content, category, type FROM educational_content WHERE id = %s',
                (content_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_educational_content(self, category: Optional[str] = None) -> List[Dict]:
        """Get all educational content with optional category filter"""
        query = 'SELECT id, title, content, category, type FROM educational_content'
        params = []

        if category:
            query += ' WHERE category = %s'
            params.append(category)

        query += ' ORDER BY category, title'

        with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_educational_categories(self) -> List[str]:
        """Get all unique educational content categories"""
        with self.conn.cursor() as cursor:
            cursor.execute(
                'SELECT DISTINCT category FROM educational_content ORDER BY category'
            )
            return [row[0] for row in cursor.fetchall()]

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
        new_type = content_type if content_type is not None else edu_content['type']

        with self.conn.cursor() as cursor:
            cursor.execute(
                '''UPDATE educational_content 
                   SET title = %s, content = %s, category = %s, type = %s 
                   WHERE id = %s''',
                (new_title, new_content, new_category, new_type, content_id)
            )
            self.conn.commit()
        return True

    def add_educational_content(self, title: str, content: str, category: str, content_type: str = 'text') -> int:
        """Add new educational content"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    'INSERT INTO educational_content (title, content, category, type) VALUES (%s, %s, %s, %s) RETURNING id',
                    (title, content, category, content_type)
                )
                result = cursor.fetchone()
                content_id = result[0] if result else 0
                self.conn.commit()
                return content_id
        except Exception as e:
            logging.error(f"Error adding educational content: {e}")
            self.conn.rollback()
            return 0
            
    def delete_educational_content(self, content_id: int) -> bool:
        """Delete educational content"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute('DELETE FROM educational_content WHERE id = %s', (content_id,))
                self.conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error deleting educational content: {e}")
            self.conn.rollback()
            return False

    def get_static_content(self, content_type: str) -> str:
        """Get static content (contact/about)"""
        # Define default content
        CONTACT_DEFAULT = "برای تماس با ما از اطلاعات زیر استفاده کنید."
        ABOUT_DEFAULT = "درباره ما - اطلاعات کامل‌تر به زودی اضافه خواهد شد."
        
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    'SELECT content FROM static_content WHERE type = %s',
                    (content_type,)
                )
                row = cursor.fetchone()
                if row and row[0]:
                    return row[0]
                else:
                    return CONTACT_DEFAULT if content_type == 'contact' else ABOUT_DEFAULT
        except Exception as e:
            logging.error(f"Error getting static content: {e}")
            return CONTACT_DEFAULT if content_type == 'contact' else ABOUT_DEFAULT

    def update_static_content(self, content_type: str, content: str) -> bool:
        """Update static content (contact/about)"""
        if content_type not in ['contact', 'about']:
            return False

        with self.conn.cursor() as cursor:
            cursor.execute(
                'UPDATE static_content SET content = %s WHERE type = %s',
                (content, content_type)
            )
            self.conn.commit()
        return True

    def export_to_csv(self, entity_type: str, filepath: str) -> bool:
        """Export data to CSV"""
        try:
            if entity_type == 'products':
                with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    cursor.execute(
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
                with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    cursor.execute(
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
                    fieldnames = ['id', 'user_id', 'name', 'phone', 'description', 'product_id', 'product_name', 'date']
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
                                product_type = row.get('type', 'product')
                                if product_type == 'service':
                                    self.add_service(
                                        name=row['name'],
                                        price=int(row['price']),
                                        description=row.get('description', ''),
                                        category_id=category_id,
                                        photo_url=row.get('photo_url', '')
                                    )
                                else:
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

                    # First pass: create all categories without parent relationships
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

                    # Second pass: update parent relationships
                    csvfile.seek(0)
                    next(reader)  # Skip header
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