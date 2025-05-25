#!/bin/bash

# Script to fix 403 Forbidden and ensure admin panel works
# Save as: /root/rfbot_fix.sh
# Run: sudo bash /root/rfbot_fix.sh

LOG_FILE="/tmp/rfbot_fix_$(date +%Y%m%d_%H%M%S).log"
PROJECT_DIR="/var/www/rfbot"
ENV_FILE="$PROJECT_DIR/.env"
NGINX_CONF="/etc/nginx/sites-available/rfbot"
NGINX_LINK="/etc/nginx/sites-enabled/rfbot"
GUNICORN_SERVICE="/etc/systemd/system/rfbot-web.service"
DB_USER="neondb_owner"
DB_NAME="neondb"
DB_PASS="npg_nguJUcZGPX83"
ADMIN_PASS="admin123"
PORT="5000"

log() { echo "$1" | tee -a $LOG_FILE; }

log "Starting RFbot fix script... Log: $LOG_FILE"

# 1. Install dependencies
log "Installing dependencies..."
apt update
apt install -y python3 python3-pip python3-venv postgresql-client nginx
cd $PROJECT_DIR
[ -d venv ] || python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt bcrypt psycopg2-binary python-dotenv gunicorn flask flask-login flask-wtf
deactivate
log "Dependencies installed."

# 2. Update .env file
log "Updating .env file..."
[ -f "$ENV_FILE" ] && cp $ENV_FILE ${ENV_FILE}.backup_$(date +%Y%m%d_%H%M%S)
cat > $ENV_FILE << EOL
DATABASE_URL=postgresql://$DB_USER:$DB_PASS@localhost:5432/$DB_NAME
SQLALCHEMY_DATABASE_URI=postgresql://$DB_USER:$DB_PASS@localhost:5432/$DB_NAME
PORT=$PORT
HOST=0.0.0.0
EOL
chown www-data:www-data $ENV_FILE
chmod 640 $ENV_FILE
log ".env updated."

# 3. Fix PostgreSQL
log "Testing DB connection..."
if echo "SELECT 1;" | PGPASSWORD=$DB_PASS psql -U $DB_USER -d $DB_NAME -h localhost >/dev/null 2>&1; then
    log "DB connection OK."
else
    log "ERROR: DB connection failed!"
    exit 1
fi

# 4. Create admin user
log "Creating admin user..."
cd $PROJECT_DIR
source venv/bin/activate
python3 -c "
import bcrypt
from app import db
from models import User
with app.app_context():
    hashed = bcrypt.hashpw('$ADMIN_PASS'.encode(), bcrypt.gensalt()).decode()
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@example.com', is_admin=True)
        admin.password = hashed
        db.session.add(admin)
    else:
        admin.password = hashed
    db.session.commit()
" >> $LOG_FILE 2>&1
if [ $? -eq 0 ]; then
    log "Admin user created."
else
    log "ERROR: Failed to create admin user!"
    exit 1
fi
deactivate

# 5. Fix Nginx config
log "Configuring Nginx..."
cat > $NGINX_CONF << EOL
upstream rfbot_app {
    server 127.0.0.1:$PORT;
}
server {
    listen 80;
    server_name _;
    client_max_body_size 20M;
    location / {
        proxy_pass http://rfbot_app;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    location /static {
        alias $PROJECT_DIR/static;
    }
}
EOL
[ -L "$NGINX_LINK" ] || ln -s $NGINX_CONF $NGINX_LINK
if nginx -t >> $LOG_FILE 2>&1; then
    log "Nginx config valid."
else
    log "ERROR: Invalid Nginx config!"
    exit 1
fi

# 6. Fix permissions
log "Fixing permissions..."
chown -R www-data:www-data $PROJECT_DIR
chmod -R 755 $PROJECT_DIR
find $PROJECT_DIR/static $PROJECT_DIR/templates -type f -exec chmod 644 {} \;
log "Permissions fixed."

# 7. Restart services
log "Restarting services..."
systemctl daemon-reload
systemctl restart rfbot-web nginx
if systemctl is-active --quiet rfbot-web && systemctl is-active --quiet nginx; then
    log "Services restarted."
else
    log "ERROR: Failed to restart services!"
    exit 1
fi

# 8. Test admin panel
log "Testing admin panel..."
SERVER_IP=$(curl -s ifconfig.me || echo "your_server_ip")
if curl -s -o /dev/null -w "%{http_code}" http://$SERVER_IP/admin | grep -q "200"; then
    log "Admin panel accessible at http://$SERVER_IP/admin"
else
    log "WARNING: Admin panel not accessible! Check $LOG_FILE, Nginx logs, and Gunicorn."
fi

log "Fix complete. Login: admin, $ADMIN_PASS"
log "Check logs: tail -n 20 /var/log/nginx/error.log, journalctl -u rfbot-web -n 50"
exit 0
