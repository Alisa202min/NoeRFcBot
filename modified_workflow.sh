#!/bin/bash
# Modified workflow script to run the simple Flask application

# Start the gunicorn server with our simplified Flask app
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main_simple:app