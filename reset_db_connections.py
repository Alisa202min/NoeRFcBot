"""
ریست کردن اتصالات پایگاه داده
این اسکریپت اتصالات فعال به پایگاه داده را قطع می‌کند
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

def reset_database_connections():
    """قطع کردن تمام اتصالات فعال به پایگاه داده"""
    conn = None
    cursor = None
    try:
        # Connect to the database
        database_url = os.environ.get("DATABASE_URL")
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Get database name from connection string
        db_name = database_url.split('/')[-1].split('?')[0]
        
        # Terminate all connections to the database except our own
        cursor.execute("""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE pid <> pg_backend_pid()
            AND datname = %s
        """, (db_name,))
        
        logger.info("All connections to the database have been terminated")
        
    except Exception as e:
        logger.error(f"Error resetting database connections: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    reset_database_connections()