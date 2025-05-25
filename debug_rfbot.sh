#!/bin/bash

# Diagnostic script for rfbot-web 502 Bad Gateway issue
# Save as: /root/rfbot_diagnose.sh
# Run: sudo bash /root/rfbot_diagnose.sh

LOG_FILE="/tmp/rfbot_diagnose_$(date +%Y%m%d_%H%M%S).log"
PROJECT_DIR="/var/www/rfbot"
ENV_FILE="$PROJECT_DIR/.env"
NGINX_CONF="/etc/nginx/sites-available/rfbot"
GUNICORN_SERVICE="/etc/systemd/system/rfbot-web.service"

echo "Starting RFbot diagnostic..." | tee -a $LOG_FILE
echo "Log file: $LOG_FILE"
echo "Timestamp: $(date)" | tee -a $LOG_FILE
echo "----------------------------------------" | tee -a $LOG_FILE

# Function to log and print messages
log() {
    echo "$1" | tee -a $LOG_FILE
}

# 1. Check rfbot-web service status
log "Checking rfbot-web service status..."
sudo systemctl status rfbot-web --no-pager >> $LOG_FILE 2>&1
if systemctl is-active --quiet rfbot-web; then
    log "rfbot-web service is active."
else
    log "ERROR: rfbot-web service is not active!"
    log "Suggestion: Run 'sudo systemctl restart rfbot-web' and check logs."
fi

# 2. Check Gunicorn logs
log "Checking Gunicorn logs (last 20 lines)..."
sudo journalctl -u rfbot-web --since "2025-05-24 21:25:00" -n 20 >> $LOG_FILE 2>&1
if sudo journalctl -u rfbot-web --since "2025-05-24 21:25:00" | grep -i "error"; then
    log "WARNING: Errors found in Gunicorn logs!"
    log "Suggestion: Review logs for Python errors (e.g., ModuleNotFound, DB issues)."
fi

# 3. Check Nginx status and logs
log "Checking Nginx service status..."
sudo systemctl status nginx --no-pager >> $LOG_FILE 2>&1
if systemctl is-active --quiet nginx; then
    log "Nginx service is active."
else
    log "ERROR: Nginx service is not active!"
    log "Suggestion: Run 'sudo systemctl start nginx'."
fi

log "Checking Nginx error logs (last 20 lines)..."
sudo tail -n 20 /var/log/nginx/error.log >> $LOG_FILE 2>&1
if sudo tail -n 20 /var/log/nginx/error.log | grep -i "connect.*refused"; then
    log "ERROR: Nginx cannot connect to Gunicorn (connection refused)!"
    log "Suggestion: Check Gunicorn bind address/port or socket."
fi

# 4. Validate Nginx configuration
log "Validating Nginx configuration..."
if [ -f "$NGINX_CONF" ]; then
    sudo nginx -t >> $LOG_FILE 2>&1
    if [ $? -eq 0 ]; then
        log "Nginx configuration is valid."
    else
        log "ERROR: Invalid Nginx configuration!"
        log "Suggestion: Check $NGINX_CONF for syntax errors."
    fi
    # Check upstream configuration
    UPSTREAM=$(grep -A 2 "upstream rfbot_app" $NGINX_CONF | grep "server" | awk '{print $2}' | tr -d ';')
    log "Nginx upstream: $UPSTREAM"
else
    log "ERROR: Nginx config file $NGINX_CONF not found!"
    log "Suggestion: Verify automate_setup.sh created the config."
fi

# 5. Check Gunicorn service configuration
log "Checking Gunicorn service configuration..."
if [ -f "$GUNICORN_SERVICE" ]; then
    GUNICORN_BIND=$(grep "ExecStart" $GUNICORN_SERVICE | grep -o -- "--bind [^ ]*" | awk '{print $2}')
    log "Gunicorn bind: $GUNICORN_BIND"
    if [ "$UPSTREAM" != "$GUNICORN_BIND" ]; then
        log "WARNING: Nginx upstream ($UPSTREAM) does not match Gunicorn bind ($GUNICORN_BIND)!"
        log "Suggestion: Align bind address in $GUNICORN_SERVICE and $NGINX_CONF."
    fi
else
    log "ERROR: Gunicorn service file $GUNICORN_SERVICE not found!"
fi

# 6. Check .env file
log "Checking .env file..."
if [ -f "$ENV_FILE" ]; then
    log ".env file exists."
    if grep -q "DATABASE_URL" $ENV_FILE; then
        log "DATABASE_URL is set."
    else
        log "ERROR: DATABASE_URL not set in .env!"
        log "Suggestion: Add 'DATABASE_URL=postgresql://neondb_owner:<password>@localhost:5432/neondb'."
    fi
    if grep -q "PORT" $ENV_FILE; then
        ENV_PORT=$(grep "PORT" $ENV_FILE | cut -d'=' -f2)
        log "PORT in .env: $ENV_PORT"
    else
        log "WARNING: PORT not set in .env, may default to 8000."
    fi
else
    log "ERROR: .env file not found at $ENV_FILE!"
    log "Suggestion: Verify automate_setup.sh created .env."
fi

# 7. Check database connection
log "Testing database connection..."
DB_USER=$(grep "DATABASE_URL" $ENV_FILE | grep -o "neondb_owner")
DB_NAME=$(grep "DATABASE_URL" $ENV_FILE | grep -o "neondb")
if sudo -u postgres psql -U $DB_USER -d $DB_NAME -c "SELECT 1;" >> $LOG_FILE 2>&1; then
    log "Database connection successful."
else
    log "ERROR: Database connection failed!"
    log "Suggestion: Check DATABASE_URL in .env and PostgreSQL status."
fi

# 8. Check ports
log "Checking open ports..."
sudo netstat -tuln | grep -E "80|8000" >> $LOG_FILE 2>&1
if sudo netstat -tuln | grep -q ":8000"; then
    log "Port 8000 is open."
else
    log "WARNING: Port 8000 is not open!"
    log "Suggestion: Ensure Gunicorn is running on port 8000."
fi
if sudo netstat -tuln | grep -q ":80"; then
    log "Port 80 is open."
else
    log "WARNING: Port 80 is not open!"
    log "Suggestion: Ensure Nginx is running and listening on port 80."
fi

# 9. Check firewall
log "Checking firewall status..."
if command -v ufw >/dev/null && sudo ufw status | grep -q "active"; then
    log "UFW is active."
    if sudo ufw status | grep -q "80.*ALLOW"; then
        log "Port 80 is allowed in UFW."
    else
        log "WARNING: Port 80 is not allowed in UFW!"
        log "Suggestion: Run 'sudo ufw allow 80'."
    fi
    if sudo ufw status | grep -q "8000.*ALLOW"; then
        log "Port 8000 is allowed in UFW."
    else
        log "WARNING: Port 8000 is not allowed in UFW!"
        log "Suggestion: Run 'sudo ufw allow 8000'."
    fi
else
    log "UFW is inactive or not installed."
fi

# 10. Check socket (if used)
log "Checking for Unix socket..."
if grep -q "unix:/var/www/rfbot/rfbot.sock" $GUNICORN_SERVICE || grep -q "unix:/var/www/rfbot/rfbot.sock" $NGINX_CONF; then
    if [ -S "/var/www/rfbot/rfbot.sock" ]; then
        log "Unix socket exists."
        SOCKET_PERMS=$(ls -l /var/www/rfbot/rfbot.sock | awk '{print $1}')
        log "Socket permissions: $SOCKET_PERMS"
        if [[ "$SOCKET_PERMS" != *"rw-rw-rw-"* ]]; then
            log "WARNING: Socket permissions may be restrictive!"
            log "Suggestion: Run 'sudo chmod 666 /var/www/rfbot/rfbot.sock'."
        fi
    else
        log "ERROR: Unix socket /var/www/rfbot/rfbot.sock not found!"
        log "Suggestion: Check Gunicorn is running and creating the socket."
    fi
else
    log "No Unix socket configured."
fi

# 11. Check admin user
log "Checking admin user in database..."
if sudo -u postgres psql -U neondb_owner -d neondb -c "SELECT username FROM users WHERE username='admin' AND role='admin';" | grep -q "admin"; then
    log "Admin user exists in database."
else
    log "WARNING: Admin user not found!"
    log "Suggestion: Run 'psql -U neondb_owner -d neondb' and insert: INSERT INTO users (username, password, role) VALUES ('admin', '<hashed_password>', 'admin');"
    log "To hash password, run: python3 -c \"import bcrypt; print(bcrypt.hashpw('your_password'.encode(), bcrypt.gensalt()).decode())\""
fi

# 12. Test Gunicorn manually
log "Testing Gunicorn manually..."
cd $PROJECT_DIR
source venv/bin/activate
gunicorn --bind 127.0.0.1:8000 app:app >> $LOG_FILE 2>&1 &
GUNICORN_PID=$!
sleep 3
if ps -p $GUNICORN_PID > /dev/null; then
    log "Gunicorn started successfully on 127.0.0.1:8000."
    log "Suggestion: Test http://<SERVER_IP>:8000/admin in browser."
else
    log "ERROR: Gunicorn failed to start!"
    log "Suggestion: Check $LOG_FILE for Python errors."
fi
kill $GUNICORN_PID 2>/dev/null

# 13. Check file permissions
log "Checking project directory permissions..."
PERMS=$(ls -ld $PROJECT_DIR | awk '{print $1}')
log "Project directory permissions: $PERMS"
if [[ "$PERMS" != *"drwxr-xr-x"* ]]; then
    log "WARNING: Project directory permissions may be incorrect!"
    log "Suggestion: Run 'sudo chown -R www-data:www-data $PROJECT_DIR' and 'sudo chmod -R 755 $PROJECT_DIR'."
fi

# 14. Check requirements
log "Checking Python dependencies..."
cd $PROJECT_DIR
source venv/bin/activate
pip check >> $LOG_FILE 2>&1
if [ $? -eq 0 ]; then
    log "All Python dependencies are satisfied."
else
    log "WARNING: Python dependency issues detected!"
    log "Suggestion: Run 'pip install -r requirements.txt' in $PROJECT_DIR/venv."
fi

# Final summary
log "----------------------------------------"
log "Diagnostic complete. Review $LOG_FILE for details."
log "Common next steps:"
log "- Check $LOG_FILE for errors and follow suggestions."
log "- Restart services: 'sudo systemctl restart rfbot-web' and 'sudo systemctl restart nginx'."
log "- Test panel: http://<SERVER_IP>/admin"
log "- If issues persist, share $LOG_FILE with support."

exit 0
