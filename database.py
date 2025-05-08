import sqlite3
import os
import csv
import logging
from typing import List, Dict, Tuple, Optional, Any, Union
import configuration

class Database:
    def __init__(self, db_path: str = configuration.DATABASE_PATH):
        """Initialize database connection."""
        self.db_path = db_path
        self._create_db_if_not_exists()
        
    def _create_db_if_not_exists(self):
        """Create database and tables if they don't exist."""
        if not os.path.exists(os.path.dirname(self.db_path)):
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
        conn = self._get_connection()
        try:
            # Read schema.sql and execute
            with open('schema.sql', 'r') as f:
                schema = f.read()
                conn.executescript(schema)
            conn.commit()
        except Exception as e:
            logging.error(f"Error creating database: {e}")
            raise
        finally:
            conn.close()
            
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # Category methods
    def get_categories(self, category_type: str, parent_id: Optional[int] = None) -> List[Dict]:
        """
        Get categories of specified type and parent.
        
        Args:
            category_type: 'product', 'service', or 'edu'
            parent_id: Parent category ID or None for root categories
        
        Returns:
            List of categories as dictionaries
        """
        conn = self._get_connection()
        try:
            table_name = f"{category_type}_categories"
            query = f"SELECT * FROM {table_name} WHERE parent_id IS ?"
            if parent_id is not None:
                query = f"SELECT * FROM {table_name} WHERE parent_id = ?"
                
            cursor = conn.execute(query, (parent_id,))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error fetching {category_type} categories: {e}")
            return []
        finally:
            conn.close()
    
    def get_category(self, category_type: str, category_id: int) -> Optional[Dict]:
        """Get a specific category by ID."""
        conn = self._get_connection()
        try:
            table_name = f"{category_type}_categories"
            cursor = conn.execute(f"SELECT * FROM {table_name} WHERE id = ?", (category_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logging.error(f"Error fetching {category_type} category {category_id}: {e}")
            return None
        finally:
            conn.close()
    
    def get_category_path(self, category_type: str, category_id: int) -> List[Dict]:
        """Get the complete path of categories from root to the specified category."""
        path = []
        current_cat = self.get_category(category_type, category_id)
        
        while current_cat:
            path.insert(0, current_cat)
            if current_cat['parent_id'] is None:
                break
            current_cat = self.get_category(category_type, current_cat['parent_id'])
            
        return path
    
    def add_category(self, category_type: str, name: str, parent_id: Optional[int] = None) -> int:
        """Add a new category and return its ID."""
        conn = self._get_connection()
        try:
            table_name = f"{category_type}_categories"
            
            # Determine level
            level = 1
            if parent_id is not None:
                parent = self.get_category(category_type, parent_id)
                if parent and 'level' in parent:
                    level = parent['level'] + 1
            
            # Only product and service categories have level field
            if category_type in ['product', 'service']:
                cursor = conn.execute(
                    f"INSERT INTO {table_name} (name, parent_id, level) VALUES (?, ?, ?)",
                    (name, parent_id, level)
                )
            else:
                cursor = conn.execute(
                    f"INSERT INTO {table_name} (name, parent_id) VALUES (?, ?)",
                    (name, parent_id)
                )
                
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            logging.error(f"Error adding {category_type} category: {e}")
            raise
        finally:
            conn.close()
    
    def update_category(self, category_type: str, category_id: int, name: str) -> bool:
        """Update a category name."""
        conn = self._get_connection()
        try:
            table_name = f"{category_type}_categories"
            conn.execute(
                f"UPDATE {table_name} SET name = ? WHERE id = ?",
                (name, category_id)
            )
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logging.error(f"Error updating {category_type} category {category_id}: {e}")
            return False
        finally:
            conn.close()
    
    def delete_category(self, category_type: str, category_id: int) -> bool:
        """Delete a category and all its children."""
        conn = self._get_connection()
        try:
            table_name = f"{category_type}_categories"
            conn.execute(f"DELETE FROM {table_name} WHERE id = ?", (category_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logging.error(f"Error deleting {category_type} category {category_id}: {e}")
            return False
        finally:
            conn.close()
    
    # Product methods
    def get_products(self, category_id: int) -> List[Dict]:
        """Get all products in a category."""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "SELECT * FROM products WHERE category_id = ?",
                (category_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error fetching products for category {category_id}: {e}")
            return []
        finally:
            conn.close()
    
    def get_product(self, product_id: int) -> Optional[Dict]:
        """Get a specific product by ID."""
        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logging.error(f"Error fetching product {product_id}: {e}")
            return None
        finally:
            conn.close()
    
    def add_product(self, category_id: int, name: str, description: str, 
                    price: Optional[str] = None, image_path: Optional[str] = None) -> int:
        """Add a new product and return its ID."""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "INSERT INTO products (category_id, name, description, price, image_path) VALUES (?, ?, ?, ?, ?)",
                (category_id, name, description, price, image_path)
            )
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            logging.error(f"Error adding product: {e}")
            raise
        finally:
            conn.close()
    
    def update_product(self, product_id: int, name: str, description: str, 
                      price: Optional[str] = None, image_path: Optional[str] = None) -> bool:
        """Update product details."""
        conn = self._get_connection()
        try:
            conn.execute(
                "UPDATE products SET name = ?, description = ?, price = ?, image_path = ? WHERE id = ?",
                (name, description, price, image_path, product_id)
            )
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logging.error(f"Error updating product {product_id}: {e}")
            return False
        finally:
            conn.close()
    
    def delete_product(self, product_id: int) -> bool:
        """Delete a product."""
        conn = self._get_connection()
        try:
            conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logging.error(f"Error deleting product {product_id}: {e}")
            return False
        finally:
            conn.close()
    
    # Service methods
    def get_services(self, category_id: int) -> List[Dict]:
        """Get all services in a category."""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "SELECT * FROM services WHERE category_id = ?",
                (category_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error fetching services for category {category_id}: {e}")
            return []
        finally:
            conn.close()
    
    def get_service(self, service_id: int) -> Optional[Dict]:
        """Get a specific service by ID."""
        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT * FROM services WHERE id = ?", (service_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logging.error(f"Error fetching service {service_id}: {e}")
            return None
        finally:
            conn.close()
    
    def add_service(self, category_id: int, name: str, description: str) -> int:
        """Add a new service and return its ID."""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "INSERT INTO services (category_id, name, description) VALUES (?, ?, ?)",
                (category_id, name, description)
            )
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            logging.error(f"Error adding service: {e}")
            raise
        finally:
            conn.close()
    
    def update_service(self, service_id: int, name: str, description: str) -> bool:
        """Update service details."""
        conn = self._get_connection()
        try:
            conn.execute(
                "UPDATE services SET name = ?, description = ? WHERE id = ?",
                (name, description, service_id)
            )
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logging.error(f"Error updating service {service_id}: {e}")
            return False
        finally:
            conn.close()
    
    def delete_service(self, service_id: int) -> bool:
        """Delete a service."""
        conn = self._get_connection()
        try:
            conn.execute("DELETE FROM services WHERE id = ?", (service_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logging.error(f"Error deleting service {service_id}: {e}")
            return False
        finally:
            conn.close()
    
    # Educational content methods
    def get_edu_content(self, category_id: Optional[int] = None) -> List[Dict]:
        """Get educational content, optionally filtered by category."""
        conn = self._get_connection()
        try:
            if category_id is not None:
                cursor = conn.execute(
                    "SELECT * FROM edu_content WHERE category_id = ?",
                    (category_id,)
                )
            else:
                cursor = conn.execute("SELECT * FROM edu_content")
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error fetching educational content: {e}")
            return []
        finally:
            conn.close()
    
    def get_edu_item(self, item_id: int) -> Optional[Dict]:
        """Get a specific educational content item."""
        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT * FROM edu_content WHERE id = ?", (item_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logging.error(f"Error fetching educational content {item_id}: {e}")
            return None
        finally:
            conn.close()
    
    def add_edu_content(self, category_id: int, title: str, description: str, 
                        content: str, media_path: Optional[str] = None) -> int:
        """Add new educational content."""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "INSERT INTO edu_content (category_id, title, description, content, media_path) VALUES (?, ?, ?, ?, ?)",
                (category_id, title, description, content, media_path)
            )
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            logging.error(f"Error adding educational content: {e}")
            raise
        finally:
            conn.close()
    
    def update_edu_content(self, item_id: int, title: str, description: str, 
                          content: str, media_path: Optional[str] = None) -> bool:
        """Update educational content."""
        conn = self._get_connection()
        try:
            conn.execute(
                "UPDATE edu_content SET title = ?, description = ?, content = ?, media_path = ? WHERE id = ?",
                (title, description, content, media_path, item_id)
            )
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logging.error(f"Error updating educational content {item_id}: {e}")
            return False
        finally:
            conn.close()
    
    def delete_edu_content(self, item_id: int) -> bool:
        """Delete educational content."""
        conn = self._get_connection()
        try:
            conn.execute("DELETE FROM edu_content WHERE id = ?", (item_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logging.error(f"Error deleting educational content {item_id}: {e}")
            return False
        finally:
            conn.close()
    
    # Static content methods
    def get_static_content(self, content_type: str) -> str:
        """Get static content by type."""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "SELECT content FROM static_content WHERE type = ?",
                (content_type,)
            )
            row = cursor.fetchone()
            return row['content'] if row else ""
        except Exception as e:
            logging.error(f"Error fetching static content {content_type}: {e}")
            return ""
        finally:
            conn.close()
    
    def update_static_content(self, content_type: str, content: str) -> bool:
        """Update static content."""
        conn = self._get_connection()
        try:
            conn.execute(
                "UPDATE static_content SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE type = ?",
                (content, content_type)
            )
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logging.error(f"Error updating static content {content_type}: {e}")
            return False
        finally:
            conn.close()
    
    # Inquiry methods
    def add_inquiry(self, user_id: int, name: str, phone: str, description: str, 
                   item_type: str, item_id: int) -> int:
        """Add a new price inquiry and return its ID."""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "INSERT INTO inquiries (user_id, name, phone, description, item_type, item_id) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, name, phone, description, item_type, item_id)
            )
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            logging.error(f"Error adding inquiry: {e}")
            raise
        finally:
            conn.close()
    
    def get_inquiries(self, status: Optional[str] = None) -> List[Dict]:
        """Get all inquiries, optionally filtered by status."""
        conn = self._get_connection()
        try:
            if status:
                cursor = conn.execute(
                    "SELECT * FROM inquiries WHERE status = ? ORDER BY created_at DESC",
                    (status,)
                )
            else:
                cursor = conn.execute("SELECT * FROM inquiries ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error fetching inquiries: {e}")
            return []
        finally:
            conn.close()
    
    def update_inquiry_status(self, inquiry_id: int, status: str) -> bool:
        """Update inquiry status."""
        conn = self._get_connection()
        try:
            conn.execute(
                "UPDATE inquiries SET status = ? WHERE id = ?",
                (status, inquiry_id)
            )
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logging.error(f"Error updating inquiry status {inquiry_id}: {e}")
            return False
        finally:
            conn.close()
    
    # Search methods
    def search(self, query: str) -> Dict[str, List[Dict]]:
        """Search products and services."""
        conn = self._get_connection()
        try:
            # Search in products
            cursor_products = conn.execute(
                "SELECT * FROM products WHERE name LIKE ? OR description LIKE ?",
                (f"%{query}%", f"%{query}%")
            )
            products = [dict(row) for row in cursor_products.fetchall()]
            
            # Search in services
            cursor_services = conn.execute(
                "SELECT * FROM services WHERE name LIKE ? OR description LIKE ?",
                (f"%{query}%", f"%{query}%")
            )
            services = [dict(row) for row in cursor_services.fetchall()]
            
            return {
                'products': products,
                'services': services
            }
        except Exception as e:
            logging.error(f"Error searching for '{query}': {e}")
            return {'products': [], 'services': []}
        finally:
            conn.close()
    
    # Import methods
    def import_csv(self, file_path: str, import_type: str) -> Tuple[int, int, List[str]]:
        """
        Import data from CSV file.
        
        Args:
            file_path: Path to CSV file
            import_type: Type of data ('product' or 'service')
            
        Returns:
            Tuple of (success_count, error_count, error_messages)
        """
        success_count = 0
        error_count = 0
        error_messages = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    try:
                        if import_type == 'product':
                            # Expected CSV columns: category_id, name, description, price, image_path
                            category_id = int(row.get('category_id', 0))
                            name = row.get('name', '')
                            description = row.get('description', '')
                            price = row.get('price', '')
                            image_path = row.get('image_path', '')
                            
                            if not category_id or not name:
                                raise ValueError("Missing required fields: category_id, name")
                                
                            self.add_product(category_id, name, description, price, image_path)
                            success_count += 1
                            
                        elif import_type == 'service':
                            # Expected CSV columns: category_id, name, description
                            category_id = int(row.get('category_id', 0))
                            name = row.get('name', '')
                            description = row.get('description', '')
                            
                            if not category_id or not name:
                                raise ValueError("Missing required fields: category_id, name")
                                
                            self.add_service(category_id, name, description)
                            success_count += 1
                            
                        else:
                            raise ValueError(f"Unsupported import type: {import_type}")
                            
                    except Exception as e:
                        error_count += 1
                        error_msg = f"Error importing row {reader.line_num}: {str(e)}"
                        error_messages.append(error_msg)
                        logging.error(error_msg)
                        
            return success_count, error_count, error_messages
            
        except Exception as e:
            error_msg = f"Error importing from CSV: {str(e)}"
            logging.error(error_msg)
            return success_count, error_count + 1, [error_msg]
