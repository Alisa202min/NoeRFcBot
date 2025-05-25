#!/bin/bash

# Script to fix RFbot-web issues (502 Bad Gateway, SQLALCHEMY_DATABASE_URI, DB, ports, admin user)
# Save as: /root/rfbot_fix.sh
# Run: sudo bash /root/rfbot_fix.sh

LOG_FILE="/tmp/rfbot_fix_$(date +%Y%m%d_%H%M%S).log"
PROJECT_DIR="/var/www/rfbot"
ENV_FILE="$PROJECT_DIR/.env"
NGINX_CONF="/etc/nginx/sites-available/rfbot"
GUNICORN_SERVICE="/etc/systemd/system/rfbot-web.service"
DEF_DB_USER="neondb_owner"
DEF_DB_NAME="neondb"
DEF_PORT="5000"
DEF_ADMIN_PASS="admin123"
DEF_DB_PASS="npg_nguJUcZGPX83"

echo "Starting RFbot fix script..." | tee -a $LOG_FILE
echo "Log file: $LOG_FILE"
echo "Timestamp: $(date)" | tee -a $LOG_FILE
echo "----------------------------------------" | tee -a $LOG_FILE

# Function to log and print messages
log() {
    echo "$1" | tee -a $LOG_FILE
}

# 1. Get user inputs with defaults
log "Please provide the following details (press Enter to accept defaults):"
read -p "DB User [$DEF_DB_USER]: " -e -i "$DEF_DB_USER" DB_USER
read -p "DB Name [$DEF_DB_NAME]: " -e -i "$DEF_DB_NAME" DB_NAME
read -p "Port (5000 or 8000) [$DEF_PORT]: " -e -i "$DEF_PORT" PORT
read -p "Admin Password [$DEF_ADMIN_PASS]: " -e -i "$DEF_ADMIN_PASS" ADMIN_PASSWORD
read -sp "DB Password [$DEF_DB_PASS]: " -e -i "$DEF_DB_PASS" DB_PASSWORD
echo

# Validate inputs
if [ -z "$DB_USER" ] || [ -z "$DB_NAME" ] || [ -z "$DB_PASSWORD" ] || [ -z "$ADMIN_PASSWORD" ]; then
    log "ERROR: All fields are required!"
    exit 1
fi
if [[ "$PORT" != "5000" && "$PORT" != "8000" ]]; then
    log "ERROR: Port must be 5000 or 8000!"
    exit 1
fi

# 2. Update .env file
log "Updating .env file..."
if [ ! -f "$ENV_FILE" ]; then
    log "Creating .env file..."
    touch $ENV_FILE
    chown www-data:www-data $ENV_FILE
    chmod 640 $ENV_FILE
fi

# Backup .env file
cp $ENV_FILE ${ENV_FILE}.backup_$(date +%Y%m%d_%H%M%S)

# Update or add variables
cat > $ENV_FILE << EOL
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME
SQLALCHEMY_DATABASE_URI=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME
PORT=$PORT
HOST=0.0.0.0
EOL
log ".env file updated with DATABASE_URL, SQLALCHEMY_DATABASE_URI, and PORT."

# 3. Fix PostgreSQL authentication
log "Configuring PostgreSQL authentication..."
PG_HBA=$(find /etc/postgresql -name pg_hba.conf 2>/dev/null | head -n 1)
if [ -z "$PG_HBA" ]; then
    log "ERROR: pg_hba.conf not found!"
    log "Suggestion: Ensure PostgreSQL is installed and locate pg_hba.conf."
    exit 1
fi

# Backup pg_hba.conf
cp $PG_HBA ${PG_HBA}.backup_$(date +%Y%m%d_%H%M%S)

# Add or update authentication rule
if ! grep -q "local\s*$DB_NAME\s*$DB_USER\s*md5" $PG_HBA; then
    sed -i "/^local\s*all\s*all\s*peer/i local   $DB_NAME   $DB_USER   md5" $PG_HBA
    log "Added md5 authentication for $DB_USER in $PG_HBA."
else
    log "md5 authentication already configured."
fi

# Restart PostgreSQL
log "Restarting PostgreSQL..."
systemctl restart postgresql
if [ $? -eq 0 ]; then
    log "PostgreSQL restarted successfully."
else
    log "ERROR: Failed to restart PostgreSQL!"
    exit 1
fi

# Test database connection
log "Testing database connection..."
if echo "SELECT 1;" | PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d $DB_NAME -h localhost >/dev/null 2>&1; then
    log "Database connection successful."
else
    log "ERROR: Database connection failed!"
    log "Suggestion: Verify DB password and PostgreSQL status."
    exit 1
fi

# 4. Align Nginx and Gunicorn ports
log "Configuring Nginx and Gunicorn to use port $PORT..."
# Update Gunicorn service
if [ -f "$GUNICORN_SERVICE" ]; then
    sed -i "s/--bind [^ ]*/--bind 127.0.0.1:$PORT/" $GUNICORN_SERVICE
    log "Updated Gunicorn bind to 127.0.0.1:$PORT."
else
    log "ERROR: Gunicorn service file $GUNICORN_SERVICE not found!"
    exit 1
fi

# Update Nginx config
if [ -f "$NGINX_CONF" ]; then
    cat > $NGINX_CONF << EOL
upstream rfbot_app {
    server 127.0.0.1:$PORT;
}
server {
    listen 80;
    server_name 185.10.75.180;
    location / {
        proxy_pass http://rfbot_app;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOL
    log "Updated Nginx upstream to 127.0.0.1:$PORT."
else
    log "ERROR: Nginx config file $NGINX_CONF not found!"
    exit 1
fi

# Test Nginx config
log "Testing Nginx configuration..."
if nginx -t >> $LOG_FILE 2>&1; then
    log "Nginx configuration is valid."
else
    log "ERROR: Invalid Nginx configuration!"
    exit 1
fi

# 5. Create admin user
log "Creating admin user..."
# Generate hashed password
cd $PROJECT_DIR
source venv/bin/activate
HASHED_PASSWORD=$(python3 -c "import bcrypt; print(bcrypt.hashpw('$ADMIN_PASSWORD'.encode(), bcrypt.gensalt()).decode())")
deactivate

# Insert admin user
if echo "INSERT INTO users (username, password, role) VALUES ('admin', '$HASHED_PASSWORD', 'admin');" | PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d $DB_NAME -h localhost >> $LOG_FILE 2>&1; then
    log "Admin user created successfully."
else
    log "WARNING: Failed to create admin user!"
    log "Suggestion: Check database logs or manually insert user."
fi

# 6. Set permissions
log "Setting project directory permissions..."
chown -R www-data:www-data $PROJECT_DIR
chmod -R 755 $PROJECT_DIR
log "Permissions updated."

# 7. Restart services
log "Restarting services..."
systemctl daemon-reload
systemctl restart rfbot-web
systemctl restart nginx
if systemctl is-active --quiet rfbot-web && systemctl is-active --quiet nginx; then
    log "Services restarted successfully."
else
    log "ERROR: Failed to restart services!"
    log "Suggestion: Check 'systemctl status rfbot-web' and 'systemctl status nginx'."
    exit 1
fi

# 8. Test Gunicorn
log "Testing Gunicorn manually..."
cd $PROJECT_DIR
source venv/bin/activate
gunicorn --bind 127.0.0.1:$PORT app:app >> $LOG_FILE 2>&1 &
GUNICORN_PID=$!
sleep 3
if ps -p $GUNICORN_PID > /dev/null; then
    log "Gunicorn started successfully on 127.0.0.1:$PORT."
else
    log "ERROR: Gunicorn failed to start!"
    log "Suggestion: Check $LOG_FILE for Python errors."
    kill $GUNICORN_PID 2>/dev/null
    exit 1
fi
kill $GUNICORN_PID 2>/dev/null

# 9. Final instructions
SERVER_IP=$(curl -s ifconfig.me)
log "----------------------------------------"
log "Fix complete. Review $LOG_FILE for details."
log "Next steps:"
log "- Test the panel: http://$SERVER_IP/admin"
log "- Login with username: admin, password: $ADMIN_PASSWORD"
log "- If issues persist, share $LOG_FILE and output of:"
log "  sudo journalctl -u rfbot-web -n 50"
log "  sudo tail -n 20 /var/log/nginx/error.log"

exit 0
