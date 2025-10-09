#!/bin/bash
# Hetzner Cloud Quick Deployment Script for CheapCruises.io
# Run this on a fresh Ubuntu 22.04 Hetzner server

set -e

echo "========================================="
echo "  CheapCruises.io - Hetzner Deployment"
echo "========================================="
echo ""

# Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install dependencies
echo "📥 Installing dependencies..."
apt install -y python3 python3-pip python3-venv nginx supervisor git

# Install Playwright system dependencies
echo "🎭 Installing Playwright dependencies..."
apt install -y wget \
    libnss3 libnspr4 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 \
    libasound2 libatspi2.0-0

# Create app directory
echo "📁 Creating application directory..."
mkdir -p /var/www/cheapcruises
cd /var/www/cheapcruises

# If you have a git repo, clone it:
# git clone YOUR_REPO_URL .

# For now, assume files are uploaded manually
echo "⚠️  Please upload your application files to /var/www/cheapcruises"
echo "   Required files:"
echo "   - app.py"
echo "   - requirements.txt"
echo "   - database_async.py"
echo "   - models.py, db_models.py"
echo "   - scrapers/"
echo "   - templates/"
echo ""
echo "Press Enter when files are uploaded..."
read

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python packages
echo "📦 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install chromium

# Create .env file
echo "⚙️  Creating .env file..."
cat > .env << EOF
DATABASE_URL=sqlite+aiosqlite:///./cruises.db
ENVIRONMENT=production
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
DEBUG=False
EOF

# Initialize database
echo "💾 Initializing database..."
python3 -c "import asyncio; from database_async import init_db; asyncio.run(init_db())"
python3 init_promo_codes.py

# Run initial scrape
echo "🔍 Running initial scrape..."
python3 run_scraper.py

# Create systemd service
echo "🔧 Creating systemd service..."
cat > /etc/systemd/system/cheapcruises.service << EOF
[Unit]
Description=CheapCruises.io FastAPI Application
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/cheapcruises
Environment="PATH=/var/www/cheapcruises/venv/bin"
ExecStart=/var/www/cheapcruises/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
echo "🌐 Configuring Nginx..."
cat > /etc/nginx/sites-available/cheapcruises << 'EOF'
server {
    listen 80;
    server_name _;  # Replace with your domain

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias /var/www/cheapcruises/static;
        expires 30d;
    }
}
EOF

# Enable nginx site
ln -sf /etc/nginx/sites-available/cheapcruises /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx config
nginx -t

# Start services
echo "🚀 Starting services..."
systemctl daemon-reload
systemctl enable cheapcruises
systemctl start cheapcruises
systemctl reload nginx

# Show status
echo ""
echo "========================================="
echo "  ✅ DEPLOYMENT COMPLETE!"
echo "========================================="
echo ""
echo "Your app is now running at:"
echo "  http://YOUR_SERVER_IP"
echo ""
echo "Service status:"
systemctl status cheapcruises --no-pager | head -10
echo ""
echo "To view logs:"
echo "  journalctl -u cheapcruises -f"
echo ""
echo "To enable HTTPS (after pointing domain):"
echo "  apt install certbot python3-certbot-nginx"
echo "  certbot --nginx -d yourdomain.com"
echo ""
echo "========================================="

