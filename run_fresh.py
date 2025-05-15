#!/usr/bin/env python
"""
Simple script to run the fresh Flask application
"""

import os
import sys
from gunicorn.app.wsgiapp import WSGIApplication

if __name__ == "__main__":
    # Set up arguments for gunicorn
    sys.argv = [
        "gunicorn",
        "--bind=0.0.0.0:5000",
        "--reload",
        "run:app"
    ]
    
    # Create and run the gunicorn application
    WSGIApplication().run()