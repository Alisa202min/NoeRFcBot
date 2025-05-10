"""
Simple database connection test for RFCBot
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from app import app, db
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

def test_direct_postgres_connection():
    """Test direct connection to PostgreSQL database"""
    print("Testing direct PostgreSQL connection...")
    
    try:
        # Get database URL from environment
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL environment variable not set")
            return False
            
        print(f"Connecting to database URL: {database_url.split('@')[0]}@...")
        
        # Create a connection
        connection = psycopg2.connect(database_url)
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Execute a simple query
        cursor.execute("SELECT 1 AS result")
        result = cursor.fetchone()
        
        # Close connection
        cursor.close()
        connection.close()
        
        if result and result['result'] == 1:
            print("✅ Direct PostgreSQL connection successful")
            return True
        else:
            print("❌ Query returned unexpected result")
            return False
            
    except Exception as e:
        print(f"❌ Error connecting to database: {str(e)}")
        return False

def test_sqlalchemy_connection():
    """Test SQLAlchemy connection through Flask"""
    print("\nTesting SQLAlchemy connection...")
    
    try:
        with app.app_context():
            # Execute a simple query
            result = db.session.execute(text("SELECT 1 AS result")).fetchone()
            
            if result and result[0] == 1:
                print("✅ SQLAlchemy connection successful")
                return True
            else:
                print("❌ Query returned unexpected result")
                return False
                
    except Exception as e:
        print(f"❌ Error with SQLAlchemy connection: {str(e)}")
        return False

def test_list_tables():
    """Test listing tables in the database"""
    print("\nTesting database tables...")
    
    try:
        direct_test = test_direct_postgres_connection()
        if not direct_test:
            return False
            
        # Get database URL from environment
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL environment variable not set")
            return False
            
        # Create a connection
        connection = psycopg2.connect(database_url)
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # List all tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        
        # Close connection
        cursor.close()
        connection.close()
        
        if tables:
            print(f"Found {len(tables)} tables:")
            for table in tables:
                print(f"  - {table['table_name']}")
            return True
        else:
            print("❌ No tables found in the database")
            return False
            
    except Exception as e:
        print(f"❌ Error listing tables: {str(e)}")
        return False

if __name__ == '__main__':
    print("===== Database Connection Tests =====")
    
    # Test direct PostgreSQL connection
    direct_result = test_direct_postgres_connection()
    
    # Test SQLAlchemy connection
    sqlalchemy_result = test_sqlalchemy_connection()
    
    # Test listing tables
    tables_result = test_list_tables()
    
    # Print overall result
    print("\n===== Test Results =====")
    print(f"Direct PostgreSQL connection: {'✅ PASSED' if direct_result else '❌ FAILED'}")
    print(f"SQLAlchemy connection: {'✅ PASSED' if sqlalchemy_result else '❌ FAILED'}")
    print(f"Database tables listing: {'✅ PASSED' if tables_result else '❌ FAILED'}")
    
    # Exit with appropriate status code
    sys.exit(0 if all([direct_result, sqlalchemy_result, tables_result]) else 1)