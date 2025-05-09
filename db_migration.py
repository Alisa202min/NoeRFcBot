import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Get database connection details from environment
DATABASE_URL = os.environ.get('DATABASE_URL')

def add_new_columns():
    """Add new columns to products table"""
    conn = None
    try:
        # Connect to the database
        conn = psycopg2.connect(DATABASE_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if columns already exist
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
        existing_columns = [col[0] for col in cursor.fetchall()]
        
        # Add manufacturer column if it doesn't exist
        if 'manufacturer' not in existing_columns:
            print("Adding 'manufacturer' column...")
            cursor.execute("""
                ALTER TABLE products 
                ADD COLUMN manufacturer VARCHAR(100)
            """)
        
        # Add provider column if it doesn't exist
        if 'provider' not in existing_columns:
            print("Adding 'provider' column...")
            cursor.execute("""
                ALTER TABLE products 
                ADD COLUMN provider VARCHAR(100)
            """)
        
        # Add service_code column if it doesn't exist
        if 'service_code' not in existing_columns:
            print("Adding 'service_code' column...")
            cursor.execute("""
                ALTER TABLE products 
                ADD COLUMN service_code VARCHAR(100)
            """)
        
        # Add duration column if it doesn't exist
        if 'duration' not in existing_columns:
            print("Adding 'duration' column...")
            cursor.execute("""
                ALTER TABLE products 
                ADD COLUMN duration VARCHAR(100)
            """)
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    add_new_columns()