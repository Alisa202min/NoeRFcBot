#!/bin/bash
# Log file for the script
LOG_FILE="/tmp/web_panel_start_$(date +%Y%m%d_%H%M%S).log"
# Function to print messages
print_message() {
    echo -e "[INFO] $1" | tee -a "$LOG_FILE"
}
# Function to check and start rfbot-web service
start_services() {
    print_message "Starting services..."
    # Restart services
    systemctl daemon-reload
    systemctl restart rfbot-web rfbot-telegram nginx
    sleep 2 # Give services time to start
    if systemctl is-active --quiet rfbot-web && systemctl is-active --quiet nginx; then
        print_message "Services started successfully."
    else
        print_message "ERROR: Failed to start one or more services!"
        exit 1
    fi
}
# Function to test if the admin panel is up
test_admin_panel() {
    print_message "Testing admin panel..."
    
    SERVER_IP=$(curl -s ifconfig.me || echo "your_server_ip")
    if curl -s -o /dev/null -w "%{http_code}" http://$SERVER_IP/admin | grep -q "200"; then
        print_message "Admin panel is accessible at http://$SERVER_IP/admin"
    else
        print_message "WARNING: Admin panel not accessible! Check $LOG_FILE, Nginx logs, and Gunicorn."
    fi
}
# Start the services and test the admin panel
start_services
test_admin_panel
print_message "Web panel startup script executed."