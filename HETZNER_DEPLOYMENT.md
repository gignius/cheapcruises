# 🚀 Deploy to Hetzner Cloud (10 Minutes)

## 💰 Cost: $4.15/month

---

## 📋 Prerequisites:

1. ✅ Your CheapCruises app (ready to deploy)
2. ✅ Hetzner account (free to create)
3. ✅ Domain name (optional, can use IP address)

---

## 🚀 QUICK DEPLOYMENT (10 Minutes):

### **Step 1: Create Hetzner Server (3 minutes)**

1. **Go to:** https://console.hetzner.cloud
2. **Create Project:** "CheapCruises"
3. **Add Server:**
   - **Location:** Ashburn, VA (closest to you) or Nuremberg (EU)
   - **Image:** Ubuntu 22.04
   - **Type:** CX11 (2 GB RAM) - **$4.15/month**
   - **Networking:** IPv4 + IPv6
   - **SSH Key:** Add your key OR use password
   - **Name:** cheapcruises-prod
4. **Click:** "Create & Buy Now"
5. **Wait:** 30 seconds for server to boot
6. **Copy:** Server IP address

---

### **Step 2: Upload Your Files (2 minutes)**

**Option A: Using SCP (from your Windows machine)**
```powershell
# Zip your project
Compress-Archive -Path C:\Cheapcruises\* -DestinationPath cheapcruises.zip

# Upload to server
scp cheapcruises.zip root@YOUR_SERVER_IP:/root/

# SSH in
ssh root@YOUR_SERVER_IP

# Unzip
cd /root
apt install unzip
unzip cheapcruises.zip -d /var/www/cheapcruises
```

**Option B: Using Git (if you have a repo)**
```bash
ssh root@YOUR_SERVER_IP
cd /var/www
git clone YOUR_GITHUB_REPO cheapcruises
```

---

### **Step 3: Run Deployment Script (5 minutes)**

```bash
# SSH into server
ssh root@YOUR_SERVER_IP

# Go to app directory
cd /var/www/cheapcruises

# Make script executable
chmod +x deployment/hetzner-quick-deploy.sh

# Run deployment
./deployment/hetzner-quick-deploy.sh
```

The script will:
- ✅ Install all dependencies
- ✅ Setup Python environment
- ✅ Install Playwright + browsers
- ✅ Initialize database
- ✅ Run initial scrape
- ✅ Configure Nginx
- ✅ Setup systemd service
- ✅ Start the app

---

### **Step 4: Access Your Site**

Visit: `http://YOUR_SERVER_IP`

**You should see your CheapCruises.io site live!** 🎉

---

## 🔒 Optional: Add HTTPS (5 minutes)

### **If you have a domain:**

1. **Point domain to server:**
   - In your domain registrar (Namecheap, Cloudflare, etc.)
   - Add A record: `@` → `YOUR_SERVER_IP`
   - Add A record: `www` → `YOUR_SERVER_IP`

2. **Wait 5-10 minutes** for DNS propagation

3. **Install SSL certificate:**
```bash
ssh root@YOUR_SERVER_IP

# Update nginx config with your domain
nano /etc/nginx/sites-available/cheapcruises
# Change "server_name _;" to "server_name yourdomain.com www.yourdomain.com;"

# Get free SSL certificate
certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Follow prompts, select option 2 (redirect HTTP to HTTPS)
```

**Done! Your site now has HTTPS!** 🔒

Visit: `https://yourdomain.com`

---

## 📊 After Deployment:

### **Manage Your App:**

```bash
# View logs
journalctl -u cheapcruises -f

# Restart app
systemctl restart cheapcruises

# Stop app
systemctl stop cheapcruises

# Start app
systemctl start cheapcruises

# Check status
systemctl status cheapcruises
```

### **Update Your App:**

```bash
# SSH in
ssh root@YOUR_SERVER_IP

# Pull latest code (if using git)
cd /var/www/cheapcruises
git pull

# Or upload new files with scp

# Restart
systemctl restart cheapcruises
```

---

## 🔄 Automatic Daily Scraping:

Already configured! The app runs scrapers daily at 6 AM via APScheduler.

**To manually trigger scrape:**
```bash
cd /var/www/cheapcruises
source venv/bin/activate
python3 run_scraper.py
```

---

## 💾 Backups (Recommended):

### **Enable Hetzner Backups:**
- In Hetzner Console → Select Server → Enable Backups
- **Cost:** $0.80/month (20% of server cost)
- **Benefit:** Automatic weekly snapshots

### **Manual Database Backup:**
```bash
# Create backup
cp /var/www/cheapcruises/cruises.db /root/backup-$(date +%Y%m%d).db

# Download to your PC
scp root@YOUR_SERVER_IP:/root/backup-*.db ./backups/
```

---

## 📈 Scaling (If Needed Later):

### **Upgrade Server:**
- In Hetzner Console → Select Server → Resize
- **CX21:** 4 GB RAM - $7.50/month
- **CX31:** 8 GB RAM - $13.90/month
- Zero downtime upgrade!

---

## 🐛 Troubleshooting:

### **App not starting:**
```bash
journalctl -u cheapcruises -n 50
```

### **Nginx not working:**
```bash
nginx -t
systemctl status nginx
```

### **Database issues:**
```bash
cd /var/www/cheapcruises
source venv/bin/activate
python3 -c "import asyncio; from database_async import init_db; asyncio.run(init_db())"
```

---

## ✅ Summary:

**Hetzner Deployment:**
- ⏱️ **10 minutes** total setup time
- 💰 **$4.15/month** (+ $0.80 for backups)
- ⭐ **Easy** - simple interface
- 🚀 **Fast** - great performance
- 🔧 **Full control** - can customize everything

**Your app will be:**
- ✅ Live 24/7
- ✅ Automatically scraping daily
- ✅ Serving all 347 cruise deals
- ✅ With route map images
- ✅ Currency conversion working

---

**Ready to deploy? Just follow the steps above!** 🚢

See `deployment/hetzner-quick-deploy.sh` for the automation script.

