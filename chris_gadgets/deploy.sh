#!/bin/bash

# Gadgets Store - Deployment Script
# For production deployment on Linux servers

set -e

echo "======================================"
echo "Gadgets Store Deployment Script"
echo "======================================"

# Configuration
PROJECT_NAME="gadgets_store"
PROJECT_DIR="/var/www/gadgets_store"
VENV_DIR="$PROJECT_DIR/venv"
USER="www-data"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root or with sudo"
    exit 1
fi

# Update system
print_status "Updating system packages..."
apt-get update
apt-get upgrade -y

# Install dependencies
print_status "Installing dependencies..."
apt-get install -y python3 python3-pip python3-venv python3-dev
apt-get install -y libmysqlclient-dev  # For MySQL
apt-get install -y nginx
apt-get install -y supervisor

# Create project directory
print_status "Creating project directory..."
mkdir -p $PROJECT_DIR
chown -R $USER:$USER $PROJECT_DIR

# Setup virtual environment
print_status "Setting up virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv $VENV_DIR
fi

# Activate virtual environment
source $VENV_DIR/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files
print_status "Collecting static files..."
python manage.py collectstatic --noinput

# Run migrations
print_status "Running database migrations..."
python manage.py migrate

# Create superuser (if not exists)
print_status "Creating superuser..."
python manage.py shell << EOF
from accounts.models import User
if not User.objects.filter(email='admin@gadgetsstore.com').exists():
    User.objects.create_superuser('admin@gadgetsstore.com', 'Admin', 'User', 'admin123')
    print('Superuser created: admin@gadgetsstore.com / admin123')
else:
    print('Superuser already exists')
EOF

# Setup Gunicorn
print_status "Setting up Gunicorn..."
cat > /etc/supervisor/conf.d/gadgets_store.conf << EOF
[program:gadgets_store]
command=$VENV_DIR/bin/gunicorn --workers 3 --bind unix:$PROJECT_DIR/gadgets_store.sock gadgets_store.wsgi:application
_directory=$PROJECT_DIR
user=$USER
group=$USER
autostart=true
autorestart=true
redirect_stderr=true
EOF

# Setup Nginx
print_status "Setting up Nginx..."
cat > /etc/nginx/sites-available/gadgets_store << EOF
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root $PROJECT_DIR;
    }
    
    location /media/ {
        root $PROJECT_DIR;
    }
    
    location / {
        include proxy_params;
        proxy_pass http://unix:$PROJECT_DIR/gadgets_store.sock;
    }
}
EOF

# Enable Nginx site
ln -sf /etc/nginx/sites-available/gadgets_store /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t

# Restart services
print_status "Restarting services..."
supervisorctl reread
supervisorctl update
supervisorctl restart gadgets_store
systemctl restart nginx

# Setup firewall
print_status "Configuring firewall..."
ufw allow 'Nginx Full'
ufw allow OpenSSH
ufw --force enable

print_status "Deployment completed!"
print_status "Website: http://yourdomain.com"
print_status "Admin: http://yourdomain.com/admin/"
print_status "Superuser: admin@gadgetsstore.com / admin123"
print_warning "Please change the default password after first login!"
