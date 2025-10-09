# 🚢 CheapCruises.io - Setup & Deployment

## Quick Start (Windows)

```batch
quickstart.bat
```

Visit: http://localhost:8000

## Quick Start (Linux/Mac)

```bash
chmod +x quickstart.sh
./quickstart.sh
```

## Deploy to Hetzner Cloud ($4.15/month)

See `HETZNER_DEPLOYMENT.md` for complete guide.

**Quick deploy:**
```bash
ssh root@YOUR_SERVER_IP
git clone https://github.com/YOUR_USERNAME/cheapcruises.git
cd cheapcruises
./deployment/hetzner-quick-deploy.sh
```

## Features

- ✅ 339 cruise deals from 11 cruise lines
- ✅ 16 promo codes with user submission & voting
- ✅ Individual detail pages for each cruise
- ✅ Route map images (local storage)
- ✅ Currency conversion (AUD/USD/EUR/GBP)
- ✅ Updates every 6 hours
- ✅ Worldwide coverage

## Push to GitHub

```powershell
git remote add origin https://github.com/YOUR_USERNAME/cheapcruises.git
git branch -M main
git push -u origin main
```

