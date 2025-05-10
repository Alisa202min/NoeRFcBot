"""
مهاجرت جدول کاربران
این اسکریپت ستون phone را به جدول users اضافه می‌کند
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

def migrate_users_table():
    """اضافه کردن ستون phone به جدول users"""
    try:
        # Connect to the database
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        conn.autocommit = False
        cursor = conn.cursor()
        
        # Check if the column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='phone'
        """)
        result = cursor.fetchone()
        
        if result:
            logger.info("Column 'phone' already exists in table 'users'")
        else:
            # Add phone column
            cursor.execute("""
                ALTER TABLE users
                ADD COLUMN phone VARCHAR(15)
            """)
            logger.info("Added column 'phone' to table 'users'")
            
        # Check if the column language_code already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='language_code'
        """)
        result = cursor.fetchone()
        
        if result:
            logger.info("Column 'language_code' already exists in table 'users'")
        else:
            # Add language_code column
            cursor.execute("""
                ALTER TABLE users
                ADD COLUMN language_code VARCHAR(10)
            """)
            logger.info("Added column 'language_code' to table 'users'")
            
        # Check if the column updated_at already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='updated_at'
        """)
        result = cursor.fetchone()
        
        if result:
            logger.info("Column 'updated_at' already exists in table 'users'")
        else:
            # Add updated_at column
            cursor.execute("""
                ALTER TABLE users
                ADD COLUMN updated_at TIMESTAMP DEFAULT NOW()
            """)
            logger.info("Added column 'updated_at' to table 'users'")
        
        # Commit the changes
        conn.commit()
        logger.info("Migration completed successfully")
        
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate_users_table()