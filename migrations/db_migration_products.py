"""
مهاجرت جدول محصولات
این اسکریپت ستون‌های جدید مورد نیاز را به جدول products اضافه می‌کند
"""

import os
import psycopg2
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def migrate_products_table():
    """اضافه کردن ستون‌های مورد نیاز به جدول products"""
    conn = None
    cursor = None
    try:
        # Connect to the database
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        conn.autocommit = False
        cursor = conn.cursor()
        
        # Check if the column cat_type already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='products' AND column_name='cat_type'
        """)
        result = cursor.fetchone()
        
        if result:
            logger.info("Column 'cat_type' already exists in table 'products'")
            
            # Rename cat_type to product_type if product_type doesn't exist
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='products' AND column_name='product_type'
            """)
            product_type_exists = cursor.fetchone()
            
            if not product_type_exists:
                cursor.execute("""
                    ALTER TABLE products
                    RENAME COLUMN cat_type TO product_type
                """)
                logger.info("Renamed column 'cat_type' to 'product_type' in table 'products'")
        else:
            # Check if product_type already exists
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='products' AND column_name='product_type'
            """)
            product_type_exists = cursor.fetchone()
            
            if not product_type_exists:
                # Add product_type column
                cursor.execute("""
                    ALTER TABLE products
                    ADD COLUMN product_type VARCHAR(20) NOT NULL DEFAULT 'product'
                """)
                logger.info("Added column 'product_type' to table 'products'")
        
        # Check other required columns and add them if they don't exist
        required_columns = [
            ('brand', 'VARCHAR(100)'),
            ('model_number', 'VARCHAR(100)'),
            ('tags', 'VARCHAR(255)'),
            ('featured', 'BOOLEAN DEFAULT false'),
            ('in_stock', 'BOOLEAN DEFAULT true'),
            ('updated_at', 'TIMESTAMP DEFAULT NOW()')
        ]
        
        for column_name, column_type in required_columns:
            cursor.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='products' AND column_name='{column_name}'
            """)
            result = cursor.fetchone()
            
            if result:
                logger.info(f"Column '{column_name}' already exists in table 'products'")
            else:
                cursor.execute(f"""
                    ALTER TABLE products
                    ADD COLUMN {column_name} {column_type}
                """)
                logger.info(f"Added column '{column_name}' to table 'products'")
        
        # Commit the changes
        conn.commit()
        logger.info("Products table migration completed successfully")
        
    except Exception as e:
        logger.error(f"Error during products table migration: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate_products_table()