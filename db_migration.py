import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from datetime import datetime

# Get database connection details from environment
DATABASE_URL = os.environ.get('DATABASE_URL')

def add_new_columns():
    """Add new columns to products and categories tables"""
    conn = None
    try:
        # Connect to the database
        conn = psycopg2.connect(DATABASE_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # ---------- PRODUCTS TABLE UPDATES ----------
        
        # Check if columns already exist in products table
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='products' AND (
                column_name='manufacturer' OR 
                column_name='provider' OR 
                column_name='service_code' OR 
                column_name='duration'
            )
        """)
        existing_product_columns = [col[0] for col in cursor.fetchall()]
        
        # Add manufacturer column if it doesn't exist
        if 'manufacturer' not in existing_product_columns:
            print("Adding 'manufacturer' column to products table...")
            cursor.execute("""
                ALTER TABLE products 
                ADD COLUMN manufacturer VARCHAR(100)
            """)
        
        # Add provider column if it doesn't exist
        if 'provider' not in existing_product_columns:
            print("Adding 'provider' column to products table...")
            cursor.execute("""
                ALTER TABLE products 
                ADD COLUMN provider VARCHAR(100)
            """)
        
        # Add service_code column if it doesn't exist
        if 'service_code' not in existing_product_columns:
            print("Adding 'service_code' column to products table...")
            cursor.execute("""
                ALTER TABLE products 
                ADD COLUMN service_code VARCHAR(100)
            """)
        
        # Add duration column if it doesn't exist
        if 'duration' not in existing_product_columns:
            print("Adding 'duration' column to products table...")
            cursor.execute("""
                ALTER TABLE products 
                ADD COLUMN duration VARCHAR(100)
            """)
        
        # ---------- CATEGORIES TABLE UPDATES ----------
        
        # Check if created_at column exists in categories table
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='categories' AND column_name='created_at'
        """)
        category_created_at_exists = cursor.fetchone() is not None
        
        # Add created_at column to categories table if it doesn't exist
        if not category_created_at_exists:
            print("Adding 'created_at' column to categories table...")
            cursor.execute("""
                ALTER TABLE categories 
                ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """)
            
            # Initialize created_at for existing rows
            current_time = datetime.utcnow()
            cursor.execute("""
                UPDATE categories
                SET created_at = %s
                WHERE created_at IS NULL
            """, (current_time,))
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    add_new_columns()