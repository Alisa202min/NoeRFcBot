#!/usr/bin/env python3
"""
WSGI entry point for the application
"""

from app import app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)