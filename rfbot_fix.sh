#!/bin/bash

# Script to fix 403 Forbidden and run web app + telegram bot
# Save as: /root/rfbot_fix.sh
# Run: sudo bash /root/rfbot_fix.sh

LOG_FILE="/tmp/rfbot_fix_$(date +%Y%m%d_%H%M%S).log"
PROJECT_DIR="/var/www/rfbot"
ENV_FILE="$PROJECT_DIR/.env"
NGINX_CONF="/etc/nginx/sites-available/rfbot"
NGINX_LINK="/etc/nginx/sites-enabled/rfbot"
GUNICORN_SERVICE="/etc/systemd/system/rfbot-web.service"
TELEGRAM_SERVICE="/etc/systemd/system/rfbot-telegram.service"
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
TELEGRAM_BOT_TOKEN=your_bot_token_here
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
from main import app, db
from models import User
with app.app_context():
    hashed = bcrypt.hashpw('$ADMIN_PASS'.encode(), bcrypt.gensalt()).decode()
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@example.com', is_admin=True)
        admin.password_hash = hashed
        db.session.add(admin)
    else:
        admin.password_hash = hashed
    db.session.commit()
" >> $LOG_FILE 2>&1
if [ $? -eq 0 ]; then
    log "Admin user created."
else
    log "ERROR: Failed to create admin user!"
    exit 1
fi
deactivate

# 5. Add admin route to app.py
log "Adding admin route to app.py..."
if ! grep -q "admin_bp = Blueprint" $PROJECT_DIR/app.py; then
    cat >> $PROJECT_DIR/app.py << EOL

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@login_required
def admin_panel():
    if not current_user.is_admin:
        return redirect(url_for('login'))
    return render_template('admin.html')

@admin_bp.route('/login')
def admin_login():
    return redirect(url_for('login'))

app.register_blueprint(admin_bp)
EOL
    log "Admin route added."
else
    log "Admin route already exists."
fi

# 6. Create template files
log "Creating template files..."
mkdir -p $PROJECT_DIR/templates
cat > $PROJECT_DIR/templates/login.html << EOL
<!DOCTYPE html>
<html>
<head>
    <title>Login</title>
</head>
<body>
    <h1>Admin Login</h1>
    <form method="POST" action="{{ url_for('login') }}">
        <input type="text" name="username" placeholder="Username" required>
        <input type="password" name="password" placeholder="Password" required>
        <button type="submit">Login</button>
    </form>
</body>
</html>
EOL
cat > $PROJECT_DIR/templates/admin.html << EOL
<!DOCTYPE html>
<html>
<head>
    <title>Admin Panel</title>
</head>
<body>
    <h1>Welcome to Admin Panel</h1>
    <p>Hello, {{ current_user.username }}!</p>
    <a href="{{ url_for('logout') }}">Logout</a>
</body>
</html>
EOL
chown -R www-data:www-data $PROJECT_DIR/templates
chmod -R 644 $PROJECT_DIR/templates/*
log "Templates created."

# 7. Fix Gunicorn service
log "Configuring Gunicorn service..."
cat > $GUNICORN_SERVICE << EOL
[Unit]
Description=RFbot Web Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_DIR
EnvironmentFile=$ENV_FILE
ExecStart=$PROJECT_DIR/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:$PORT --reuse-port --reload main:app
Restart=always

[Install]
WantedBy=multi-user.target
EOL
log "Gunicorn service updated."

# 8. Fix Telegram bot service
log "Configuring Telegram bot service..."
cat > $TELEGRAM_SERVICE << EOL
[Unit]
Description=RFbot Telegram Bot
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_DIR
EnvironmentFile=$ENV_FILE
ExecStart=$PROJECT_DIR/venv/bin/python bot.py
Restart=always

[Install]
WantedBy=multi-user.target
EOL
log "Telegram bot service updated."

# 9. Fix Nginx config
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

# 10. Fix permissions
log "Fixing permissions..."
chown -R www-data:www-data $PROJECT_DIR
chmod -R 755 $PROJECT_DIR
find $PROJECT_DIR/static $PROJECT_DIR/templates -type f -exec chmod 644 {} \;
log "Permissions fixed."

# 11. Restart services
log "Restarting services..."
systemctl daemon-reload
systemctl restart rfbot-web rfbot-telegram nginx
if systemctl is-active --quiet rfbot-web && systemctl is-active --quiet rfbot-telegram && systemctl is-active --quiet nginx; then
    log "Services restarted."
else
    log "ERROR: Failed to restart services!"
    exit 1
fi

# 12. Test admin panel
log "Testing admin panel..."
SERVER_IP=$(curl -s ifconfig.me || echo "your_server_ip")
for path in "/login" "/admin/login" "/admin"; do
    if curl -s -o /dev/null -w "%{http_code}" http://$SERVER_IP$path | grep -q "200"; then
        log "Admin panel accessible at http://$SERVER_IP$path"
    else
        log "WARNING: Path $path not accessible! Check $LOG_FILE, Nginx logs, and Gunicorn."
    fi
done

log "Fix complete. Login: admin, $ADMIN_PASS"
log "Check logs: tail -n 20 /var/log/nginx/error.log, journalctl -u rfbot-web -n 50, journalctl -u rfbot-telegram -n 50"
exit 0
