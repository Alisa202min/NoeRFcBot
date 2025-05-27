#!/usr/bin/env python3
"""
Main database migration script
Creates all tables and initial structure
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from configuration import config
import models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_database_if_not_exists():
    """Create database if it doesn't exist"""
    try:
        # Parse database URL to get database name
        from urllib.parse import urlparse
        parsed = urlparse(config.DATABASE_URL)
        
        db_name = parsed.path[1:]  # Remove leading slash
        
        # Create connection URL without database name
        base_url = f"{parsed.scheme}://{parsed.netloc}/postgres"
        
        # Create engine for postgres database
        engine = create_engine(base_url)
        
        # Check if database exists
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                {"db_name": db_name}
            )
            
            if not result.fetchone():
                # Create database
                conn.execute(text("COMMIT"))  # End current transaction
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                logger.info(f"Database '{db_name}' created successfully")
            else:
                logger.info(f"Database '{db_name}' already exists")
        
        engine.dispose()
        
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        return False
    
    return True

def run_migration():
    """Run the main migration"""
    try:
        # Create database if needed
        if not create_database_if_not_exists():
            logger.error("Failed to create database")
            return False
        
        with app.app_context():
            logger.info("Starting database migration...")
            
            # Drop all tables (for fresh start)
            # db.drop_all()
            # logger.info("Dropped existing tables")
            
            # Create all tables
            db.create_all()
            logger.info("Created all tables")
            
            # Verify tables were created
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            expected_tables = [
                'users', 'categories', 'products', 'services', 'media',
                'inquiries', 'educational_content', 'static_content',
                'bot_users', 'user_sessions'
            ]
            
            missing_tables = [table for table in expected_tables if table not in tables]
            
            if missing_tables:
                logger.error(f"Missing tables: {missing_tables}")
                return False
            
            logger.info(f"Successfully created {len(tables)} tables")
            logger.info("Migration completed successfully!")
            
            return True
            
    except SQLAlchemyError as e:
        logger.error(f"Database error during migration: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during migration: {e}")
        return False

def verify_migration():
    """Verify that migration was successful"""
    try:
        with app.app_context():
            # Test basic queries
            users_count = models.User.query.count()
            categories_count = models.Category.query.count()
            products_count = models.Product.query.count()
            services_count = models.Service.query.count()
            
            logger.info(f"Verification results:")
            logger.info(f"  Users: {users_count}")
            logger.info(f"  Categories: {categories_count}")
            logger.info(f"  Products: {products_count}")
            logger.info(f"  Services: {services_count}")
            
            return True
            
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("DATABASE MIGRATION SCRIPT")
    logger.info("=" * 50)
    
    # Validate configuration
    if not config.validate():
        logger.error("Configuration validation failed")
        sys.exit(1)
    
    # Run migration
    if run_migration():
        logger.info("Migration successful!")
        
        # Verify migration
        if verify_migration():
            logger.info("Verification successful!")
        else:
            logger.warning("Verification failed, but migration might still be successful")
    else:
        logger.error("Migration failed!")
        sys.exit(1)
    
    logger.info("Migration script completed")
