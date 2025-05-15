#!/usr/bin/env python
"""
Diagnostic Flask application runner
Use this to test basic Flask functionality without the main application complexity
"""

import os
import sys
import logging
from fresh_app import app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info(f"Starting diagnostic Flask app on port 3000...")
    logger.info(f"Environment: {os.environ.get('REPL_ID', 'local')}")
    
    # Run the Flask application on a different port to avoid conflicts
    app.run(host="0.0.0.0", port=3000, debug=True)