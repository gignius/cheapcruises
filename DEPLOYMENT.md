# CheapCruises.io Deployment Guide

## Production Deployment on Hetzner Server

This guide will help you deploy CheapCruises.io to your Hetzner dedicated server.

### Prerequisites

- Hetzner dedicated server with Ubuntu 22.04 or 24.04
- Domain name (cheapcruises.io) pointed to your server's IP
- Root or sudo access

### Quick Start

1. **Clone the repository to your server:**
   ```bash
   cd /var/www
   git clone <your-repo-url> cheapcruises
   cd cheapcruises
   ```

2. **Run the deployment script:**
   ```bash
   sudo bash deployment/setup.sh
   ```

   This script will:
   - Install Python 3.11, PostgreSQL, Nginx
   - Create database and user
   - Set up virtual environment
   - Configure systemd service
   - Set up Nginx reverse proxy
   - Get Let's Encrypt SSL certificate

3. **Verify deployment:**
   ```bash
   systemctl status cheapcruises
   curl https://cheapcruises.io/api/health
   ```

---

## Manual Deployment (Step by Step)

### 1. System Setup

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install packages
sudo apt-get install -y python3.11 python3.11-venv postgresql nginx git certbot python3-certbot-nginx
```

### 2. PostgreSQL Setup

```bash
# Create database
sudo -u postgres createdb cruises

# Create user (replace with secure password)
sudo -u postgres psql -c "CREATE USER cruises WITH ENCRYPTED PASSWORD 'your_secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE cruises TO cruises;"
sudo -u postgres psql -c "ALTER DATABASE cruises OWNER TO cruises;"
```

### 3. Application Setup

```bash
# Create app directory
sudo mkdir -p /var/www/cheapcruises
cd /var/www/cheapcruises

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Environment Configuration

Create `.env` file:

```bash
sudo nano /var/www/cheapcruises/.env
```

Add:
```env
DATABASE_URL=postgresql+asyncpg://cruises:your_password@localhost/cruises
DEBUG=False
SECRET_KEY=<generate-with-openssl-rand-hex-32>
PRICE_THRESHOLD=200.0
HOST=0.0.0.0
PORT=8000
WORKERS=4
```

Set permissions:
```bash
sudo chmod 600 /var/www/cheapcruises/.env
sudo chown www-data:www-data /var/www/cheapcruises -R
```

### 5. Initialize Database

```bash
cd /var/www/cheapcruises
sudo -u www-data ./venv/bin/python -c "import asyncio; from database_async import init_db; asyncio.run(init_db())"
```

### 6. Systemd Service

```bash
# Copy service file
sudo cp deployment/systemd/cheapcruises.service /etc/systemd/system/

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable cheapcruises
sudo systemctl start cheapcruises

# Check status
sudo systemctl status cheapcruises
```

### 7. Nginx Configuration

```bash
# Copy Nginx config
sudo cp deployment/nginx/cheapcruises.conf /etc/nginx/sites-available/cheapcruises
sudo ln -s /etc/nginx/sites-available/cheapcruises /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Test config
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### 8. SSL Certificate

```bash
# Get Let's Encrypt certificate
sudo certbot --nginx -d cheapcruises.io -d www.cheapcruises.io

# Test auto-renewal
sudo certbot renew --dry-run
```

---

## Post-Deployment

### Run Initial Scrape

```bash
cd /var/www/cheapcruises
sudo -u www-data ./venv/bin/python run_scraper.py
```

### Verify Everything Works

1. Visit: https://cheapcruises.io
2. Check API: https://cheapcruises.io/api/docs
3. Check health: https://cheapcruises.io/api/health

---

## Maintenance

### View Logs

```bash
# Application logs
sudo journalctl -u cheapcruises -f

# Nginx logs
sudo tail -f /var/log/nginx/cheapcruises_access.log
sudo tail -f /var/log/nginx/cheapcruises_error.log
```

### Restart Services

```bash
# Restart application
sudo systemctl restart cheapcruises

# Reload Nginx (without downtime)
sudo systemctl reload nginx

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### Update Application

```bash
cd /var/www/cheapcruises
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart cheapcruises
```

### Database Backup

```bash
# Create backup
sudo -u postgres pg_dump cruises > backup_$(date +%Y%m%d).sql

# Restore backup
sudo -u postgres psql cruises < backup_20250109.sql
```

### Manual Scraper Run

```bash
cd /var/www/cheapcruises
sudo -u www-data ./venv/bin/python run_scraper.py
```

---

## Monitoring

### Check Service Status

```bash
sudo systemctl status cheapcruises
sudo systemctl status nginx
sudo systemctl status postgresql
```

### Check Disk Space

```bash
df -h
```

### Check Database Size

```bash
sudo -u postgres psql -c "\l+"
sudo -u postgres psql -c "SELECT pg_size_pretty(pg_database_size('cruises'));"
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u cheapcruises -n 50

# Check if port is available
sudo netstat -tlnp | grep 8000

# Test manually
cd /var/www/cheapcruises
source venv/bin/activate
./venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000
```

### Database Connection Issues

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
sudo -u postgres psql cruises -c "SELECT 1;"

# Check permissions
sudo -u postgres psql cruises -c "\du"
```

### Nginx Issues

```bash
# Test config
sudo nginx -t

# Check error log
sudo tail -f /var/log/nginx/error.log

# Restart Nginx
sudo systemctl restart nginx
```

---

## Security

### Firewall Setup (UFW)

```bash
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### Regular Updates

```bash
# Update system packages
sudo apt-get update && sudo apt-get upgrade -y

# Update Python dependencies
cd /var/www/cheapcruises
source venv/bin/activate
pip install --upgrade -r requirements.txt
sudo systemctl restart cheapcruises
```

---

## Performance Tuning

### Increase Workers (for more traffic)

Edit `/etc/systemd/system/cheapcruises.service`:
```ini
ExecStart=/var/www/cheapcruises/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000 --workers 8
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl restart cheapcruises
```

### PostgreSQL Tuning

Edit `/etc/postgresql/14/main/postgresql.conf`:
```conf
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 128MB
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

---

## Scaling

When you outgrow a single server:

1. **Add Redis for caching**
2. **Separate database to dedicated server**
3. **Use load balancer with multiple app servers**
4. **Add CDN for static files**
5. **Use managed PostgreSQL (e.g., AWS RDS)**

---

## Support

For issues or questions:
- Check logs: `sudo journalctl -u cheapcruises -f`
- API docs: https://cheapcruises.io/api/docs
- Health check: https://cheapcruises.io/api/health


