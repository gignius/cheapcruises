#!/bin/bash
# CheapCruises.io Deployment Setup Script for Hetzner Server
# Run as root or with sudo

set -e

echo "========================================="
echo "CheapCruises.io Deployment Setup"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables
APP_DIR="/var/www/cheapcruises"
APP_USER="www-data"
DB_NAME="cruises"
DB_USER="cruises"
DOMAIN="cheapcruises.io"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root or with sudo${NC}"
    exit 1
fi

echo -e "${GREEN}Step 1: Update system packages${NC}"
apt-get update
apt-get upgrade -y

echo -e "${GREEN}Step 2: Install required packages${NC}"
apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    postgresql \
    postgresql-contrib \
    nginx \
    git \
    certbot \
    python3-certbot-nginx

echo -e "${GREEN}Step 3: Create application directory${NC}"
mkdir -p $APP_DIR
cd $APP_DIR

echo -e "${GREEN}Step 4: Create Python virtual environment${NC}"
python3.11 -m venv venv
source venv/bin/activate

echo -e "${GREEN}Step 5: Set up PostgreSQL database${NC}"
# Generate random password
DB_PASSWORD=$(openssl rand -base64 32)

# Create database and user
sudo -u postgres psql <<EOF
CREATE DATABASE $DB_NAME;
CREATE USER $DB_USER WITH ENCRYPTED PASSWORD '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
ALTER DATABASE $DB_NAME OWNER TO $DB_USER;
\q
EOF

echo -e "${YELLOW}Database created:${NC}"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo "  Password: $DB_PASSWORD"
echo -e "${YELLOW}Save these credentials!${NC}"

echo -e "${GREEN}Step 6: Create .env file${NC}"
cat > $APP_DIR/.env <<EOF
APP_NAME=CheapCruises.io
DEBUG=False
DATABASE_URL=postgresql+asyncpg://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME
PRICE_THRESHOLD=200.0
SECRET_KEY=$(openssl rand -hex 32)
HOST=0.0.0.0
PORT=8000
WORKERS=4
EOF

echo -e "${GREEN}Step 7: Set permissions${NC}"
chown -R $APP_USER:$APP_USER $APP_DIR
chmod 600 $APP_DIR/.env

echo -e "${GREEN}Step 8: Install Python dependencies${NC}"
# This assumes you've already copied your code to the server
if [ -f "$APP_DIR/requirements.txt" ]; then
    $APP_DIR/venv/bin/pip install -r $APP_DIR/requirements.txt
else
    echo -e "${YELLOW}requirements.txt not found. You'll need to install dependencies manually.${NC}"
fi

echo -e "${GREEN}Step 9: Initialize database${NC}"
cd $APP_DIR
sudo -u $APP_USER $APP_DIR/venv/bin/python -c "
import asyncio
from database_async import init_db
asyncio.run(init_db())
"

echo -e "${GREEN}Step 10: Set up systemd service${NC}"
cp $APP_DIR/deployment/systemd/cheapcruises.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable cheapcruises
systemctl start cheapcruises

echo -e "${GREEN}Step 11: Configure Nginx${NC}"
cp $APP_DIR/deployment/nginx/cheapcruises.conf /etc/nginx/sites-available/cheapcruises
ln -sf /etc/nginx/sites-available/cheapcruises /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx config
nginx -t

# Reload Nginx
systemctl reload nginx

echo -e "${GREEN}Step 12: Set up SSL with Let's Encrypt${NC}"
echo -e "${YELLOW}Make sure your domain $DOMAIN points to this server's IP${NC}"
read -p "Press enter when DNS is configured..."

# Get SSL certificate
certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

# Set up auto-renewal
systemctl enable certbot.timer
systemctl start certbot.timer

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo -e "${GREEN}Your application is now running at:${NC}"
echo -e "  https://$DOMAIN"
echo ""
echo -e "${GREEN}Useful commands:${NC}"
echo "  systemctl status cheapcruises  - Check service status"
echo "  systemctl restart cheapcruises - Restart application"
echo "  journalctl -u cheapcruises -f  - View logs"
echo "  systemctl reload nginx         - Reload Nginx"
echo ""
echo -e "${YELLOW}Database credentials (save these):${NC}"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo "  Password: $DB_PASSWORD"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "1. Upload your application code to $APP_DIR"
echo "2. Install dependencies: $APP_DIR/venv/bin/pip install -r requirements.txt"
echo "3. Restart the service: systemctl restart cheapcruises"
echo "4. Run initial scrape (optional): cd $APP_DIR && sudo -u $APP_USER $APP_DIR/venv/bin/python run_scraper.py"



