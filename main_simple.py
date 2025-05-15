"""
Simplified main application entry point for RFCBot
This file is used to run the Flask application with Gunicorn
"""

import os
import sys
import logging
from flask import Flask

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create simple Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "رمز موقت برای ربات RFCBot")

@app.route('/')
def index():
    """Main index page."""
    return "RFCBot Admin Dashboard - Main Simple App"

@app.route('/health')
def health():
    """Health check endpoint."""
    return {
        "status": "ok", 
        "message": "The simple app is running correctly!",
        "database_url": os.environ.get("DATABASE_URL", "").split("@")[1] if "@" in os.environ.get("DATABASE_URL", "") else None
    }

# Only run the app directly when script is executed directly (not with Gunicorn)
if __name__ == "__main__":
    logger.info("Starting main simple Flask app...")
    app.run(host="0.0.0.0", port=5000, debug=True)