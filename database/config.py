"""
Database configuration module
This module provides functions to configure the Flask app with SQLAlchemy
"""

import os
import logging
from flask import Flask
from database import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def configure_database(app: Flask) -> None:
    """
    Configure the Flask application with SQLAlchemy
    
    Args:
        app: The Flask application instance to configure
    """
    # Configure database connection
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "connect_args": {
            "sslmode": "prefer",
            "application_name": "RFCBot",
            "connect_timeout": 10
        }
    }
    
    # Initialize the app with SQLAlchemy
    db.init_app(app)
    
    # Create tables if they don't exist
    with app.app_context():
        from database import initialize_models
        initialize_models()
        db.create_all()
        logger.info("Database tables created or verified")