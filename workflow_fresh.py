#!/usr/bin/env python
"""
Workflow script for running the fresh Flask application via Gunicorn
"""

import sys
import os
import logging
from gunicorn.app.wsgiapp import WSGIApplication

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Run the Gunicorn WSGI application with the fresh app"""
    logger.info("Starting Gunicorn with fresh_app.py")
    
    # Set up arguments for gunicorn
    sys.argv = [
        "gunicorn",
        "--bind=0.0.0.0:5000",
        "--reload",
        "fresh_app:app"
    ]
    
    # Create and run the gunicorn application
    WSGIApplication().run()

if __name__ == "__main__":
    main()