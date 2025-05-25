#!/bin/bash

# Script to fix RFbot-web issues (403 Forbidden, admin user, DB, ports)
# Save as: /root/rfbot_fix.sh
# Run: sudo bash /root/rfbot_fix.sh

LOG_FILE="/tmp/rfbot_fix_$(date +%Y%m%d_%H%M%S).log"
PROJECT_DIR="/var/www/rfbot"
ENV_FILE="$PROJECT_DIR/.env"
NGINX_CONF="/etc/nginx/sites-available/rfbot"
NGINX_LINK="/etc/nginx/sites-enabled/rfbot"
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

# 1. Install dependencies
log "Installing dependencies..."
apt update
apt install -y python3 python3-pip python3-venv postgresql-client nginx
cd $PROJECT_DIR
[ -d venv ] || python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt bcrypt psycopg2-binary python-dotenv gunicorn flask
deactivate
log "Dependencies installed."

# 2. Get user inputs with defaults
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

# 3. Update .env file
log "Updating .env file..."
if [ ! -f "$ENV_FILE" ]; then
    log "Creating .env file..."
    touch $ENV_FILE
    chown www-data:www-data $ENV_FILE
    chmod 640 $ENV_FILE
fi
cp $ENV_FILE ${ENV_FILE}.backup_$(date +%Y%m%d_%H%M%S)
cat > $ENV_FILE << EOL
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME
SQLALCHEMY_DATABASE_URI=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME
PORT=$PORT
HOST=0.0.0.0
EOL
log ".env file updated."

# 4. Fix PostgreSQL authentication
log "Configuring PostgreSQL authentication..."
PG_HBA=$(find /etc/postgresql -name pg_hba.conf 2>/dev/null | head -n 1)
if [ -z "$PG_HBA" ]; then
    log "ERROR: pg_hba.conf not found!"
    exit 1
fi
cp $PG_HBA ${PG_HBA}.backup_$(date +%Y%m%d_%H%M%S)
if ! grep -q "local\s*$DB_NAME\s*$DB_USER\s*md5" $PG_HBA; then
    sed -i "/^local\s*all\s*all\s*peer/i local   $DB_NAME   $DB_USER   md5" $PG_HBA
    log "Added md5 authentication."
else
    log "md5 authentication already configured."
fi
systemctl restart postgresql || { log "ERROR: Failed to restart PostgreSQL!"; exit 1; }
log "PostgreSQL restarted."

# Test database connection
log "Testing database connection..."
if echo "SELECT 1;" | PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d $DB_NAME -h localhost >/dev/null 2>&1; then
    log "Database connection successful."
else
    log "ERROR: Database connection failed!"
    exit 1
fi

# 5. Create admin user
log "Creating admin user..."
cd $PROJECT_DIR
source venv/bin/activate
HASHED_PASSWORD=$(python3 -c "import bcrypt; print(bcrypt.hashpw('$ADMIN_PASSWORD'.encode(), bcrypt.gensalt()).decode())" 2>> $LOG_FILE)
if [ $? -ne 0 ]; then
    log "ERROR: Failed to hash admin password!"
    deactivate
    exit 1
fi
if echo "INSERT INTO users (username, password, role) VALUES ('admin', '$HASHED_PASSWORD', 'admin') ON CONFLICT (username) DO UPDATE SET password='$HASHED_PASSWORD', role='admin';" | PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d $DB_NAME -h localhost >> $LOG_FILE 2>&1; then
    log "Admin user created."
else
    log "ERROR: Failed to create admin user!"
    deactivate
    exit 1
fi
deactivate

# 6. Align Nginx and Gunicorn ports
log "Configuring Nginx and Gunicorn to use port $PORT..."
if [ -f "$GUNICORN_SERVICE" ]; then
    sed -i "s/--bind [^ ]*/--bind 127.0.0.1:$PORT/" $GUNICORN_SERVICE
    log "Updated Gunicorn bind."
else
    log "WARNING: Gunicorn service not found! Creating default service."
    cat > $GUNICORN_SERVICE << EOL
[Unit]
Description=RFbot Web Gunicorn
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/gunicorn --bind 127.0.0.1:$PORT app:app

[Install]
WantedBy=multi-user.target
EOL
    log "Gunicorn service created."
fi
if [ -f "$NGINX_CONF" ]; then
    cat > $NGINX_CONF << EOL
upstream rfbot_app {
    server 127.0.0.1:$PORT;
}
server {
    listen 80;
    server_name _;
    location / {
        proxy_pass http://rfbot_app;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOL
    log "Updated Nginx config."
    [ -L "$NGINX_LINK" ] || ln -s $NGINX_CONF $NGINX_LINK
else
    log "ERROR: Nginx config not found!"
    exit 1
fi
if nginx -t >> $LOG_FILE 2>&1; then
    log "Nginx configuration valid."
else
    log "ERROR: Invalid Nginx configuration!"
    exit 1
fi

# 7. Set permissions
log "Setting permissions..."
chown -R www-data:www-data $PROJECT_DIR
chmod -R 755 $PROJECT_DIR
find $PROJECT_DIR/static $PROJECT_DIR/templates -type f -exec chmod 644 {} \;
log "Permissions updated."

# 8. Restart services
log "Restarting services..."
systemctl daemon-reload
systemctl restart rfbot-web nginx
if systemctl is-active --quiet rfbot-web && systemctl is-active --quiet nginx; then
    log "Services restarted."
else
    log "ERROR: Failed to restart services!"
    exit 1
fi

# 9. Test Gunicorn
log "Testing Gunicorn..."
cd $PROJECT_DIR
source venv/bin/activate
gunicorn --bind 127.0.0.1:$PORT app:app >> $LOG_FILE 2>&1 &
GUNICORN_PID=$!
sleep 3
if ps -p $GUNICORN_PID > /dev/null; then
    log "Gunicorn started on 127.0.1:$PORT."
else
    log "ERROR: Gunicorn failed to start!"
    kill $GUNICORN_PID 2>/dev/null
    deactivate
    exit 1
fi
kill $GUNICORN_PID 2>/dev/null
deactivate

# 10. Test admin panel
log "Testing admin panel..."
SERVER_IP=$(curl -s ifconfig.me || echo "your_server_ip")
ADMIN_RESPONSE=$(curl -s -w "%{http_code}" http://127.0.0.1:$PORT/admin -o /dev/null)
if [ "$ADMIN_RESPONSE" = "200" ]; then
    log "Admin panel accessible locally."
else
    log "WARNING: Admin panel not accessible locally (HTTP $ADMIN_RESPONSE)! Check app.py or logs."
fi

# 11. Final instructions
log "----------------------------------------"
log "Fix complete. Review $LOG_FILE."
log "Next steps:"
log "- Test panel: http://$SERVER_IP/admin"
log "- Login: admin, $ADMIN_PASSWORD"
log "- If 403 persists, check:"
log "  sudo tail -n 20 /var/log/nginx/error.log"
log "  sudo journalctl -u rfbot-web -n 50"
log "  grep -r 'admin' $PROJECT_DIR/*.py"

exit 0
