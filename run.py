#!/usr/bin/env python
"""
Main Flask application runner for RFCBot
This is the entry point for the web application component
"""

import os
import sys
import logging
from flask import Flask, render_template, jsonify

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "رمز موقت برای ربات RFCBot")

# Simple routes for testing
@app.route('/')
def index():
    """Main index page."""
    return "RFCBot Admin Dashboard - Main App"

@app.route('/api/health')
def health():
    """Health check endpoint."""
    return {
        "status": "ok", 
        "message": "The RFCBot admin panel is running",
        "database": os.environ.get("DATABASE_URL", "").split("@")[1] if "@" in os.environ.get("DATABASE_URL", "") else None
    }

# Run the application directly when this script is executed
if __name__ == "__main__":
    try:
        port = int(os.environ.get("PORT", 5000))
        logger.info(f"Starting Flask app on port {port}...")
        app.run(host="0.0.0.0", port=port, debug=True)
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        sys.exit(1)