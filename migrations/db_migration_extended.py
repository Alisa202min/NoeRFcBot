import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from datetime import datetime

# Get database connection details from environment
DATABASE_URL = os.environ.get('DATABASE_URL')

def add_extended_columns():
    """Add extended columns to products and services tables for enhanced search functionality"""
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
                column_name='brand' OR 
                column_name='model' OR 
                column_name='in_stock' OR 
                column_name='tags' OR
                column_name='featured'
            )
        """)
        existing_product_columns = [col[0] for col in cursor.fetchall()]
        
        # Add brand column if it doesn't exist
        if 'brand' not in existing_product_columns:
            print("Adding 'brand' column to products table...")
            cursor.execute("""
                ALTER TABLE products 
                ADD COLUMN brand VARCHAR(100)
            """)
        
        # Add model column if it doesn't exist
        if 'model' not in existing_product_columns:
            print("Adding 'model' column to products table...")
            cursor.execute("""
                ALTER TABLE products 
                ADD COLUMN model VARCHAR(100)
            """)
        
        # Add in_stock column if it doesn't exist
        if 'in_stock' not in existing_product_columns:
            print("Adding 'in_stock' column to products table...")
            cursor.execute("""
                ALTER TABLE products 
                ADD COLUMN in_stock BOOLEAN DEFAULT TRUE
            """)
        
        # Add tags column if it doesn't exist
        if 'tags' not in existing_product_columns:
            print("Adding 'tags' column to products table...")
            cursor.execute("""
                ALTER TABLE products 
                ADD COLUMN tags TEXT
            """)
        
        # Add featured column if it doesn't exist
        if 'featured' not in existing_product_columns:
            print("Adding 'featured' column to products table...")
            cursor.execute("""
                ALTER TABLE products 
                ADD COLUMN featured BOOLEAN DEFAULT FALSE
            """)
            
        # Check for cat_type column
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='products' AND column_name='product_type'
        """)
        product_type_exists = cursor.fetchone() is not None
        
        # Add product_type column if it doesn't exist
        if not product_type_exists:
            print("Adding 'product_type' column to products table...")
            cursor.execute("""
                ALTER TABLE products 
                ADD COLUMN product_type VARCHAR(20) DEFAULT 'product'
            """)
            
            # Update product_type for existing records
            cursor.execute("""
                UPDATE products
                SET product_type = 'product'
                WHERE product_type IS NULL
            """)
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    add_extended_columns()