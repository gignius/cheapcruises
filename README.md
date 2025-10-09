# 🚢 CheapCruises.io

Automated cruise deal aggregator that scrapes and displays cruise deals from 11 major cruise lines.

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## ✨ Features

- 🔍 **Multi-page web scraping** - Extracts 347+ cruise deals from OzCruising.com.au
- 🖼️ **Route map images** - Automatically extracts cruise route photos
- 💱 **Multi-currency** - Support for AUD, USD, EUR, GBP
- 🎯 **Advanced filtering** - Filter by cruise line, duration, price, port
- ⚡ **Fast & Async** - FastAPI + SQLAlchemy async
- 📅 **Auto-updates** - Daily automated scraping at 6 AM
- 🎨 **Modern UI** - Tailwind CSS + Alpine.js

## 🌍 Cruise Lines Covered (11 Total)

- Carnival
- Royal Caribbean
- Norwegian Cruise Line
- Holland America
- Celebrity Cruises
- Princess Cruises
- MSC Cruises
- Cunard
- P&O Australia
- Seabourn
- Viking Ocean Cruises
- Azamara

## 🚀 Quick Start

### **Prerequisites:**
- Python 3.11+
- pip

### **Windows:**
```batch
quickstart.bat
```

### **Linux/Mac:**
```bash
chmod +x quickstart.sh
./quickstart.sh
```

Visit: http://localhost:8000

## 📦 Tech Stack

- **Backend:** FastAPI, Uvicorn
- **Database:** SQLite (async with aiosqlite)
- **ORM:** SQLAlchemy 2.0 (async)
- **Scraping:** BeautifulSoup4, lxml, Playwright
- **Scheduling:** APScheduler
- **Frontend:** Tailwind CSS, Alpine.js

## 🏗️ Architecture

```
CheapCruises.io
├── app.py              # FastAPI application
├── database_async.py   # Async database layer
├── scheduler.py        # Background job scheduler
├── scrapers/
│   └── ozcruising_scraper.py  # Main scraper
├── templates/          # HTML templates
└── extract_ozcruising_images.py  # Route map extractor
```

## 🔧 Manual Setup

1. **Clone repository:**
```bash
git clone https://github.com/YOUR_USERNAME/cheapcruises.git
cd cheapcruises
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
.\venv\Scripts\activate  # Windows
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
playwright install chromium
```

4. **Initialize database:**
```bash
python -c "import asyncio; from database_async import init_db; asyncio.run(init_db())"
python init_promo_codes.py
```

5. **Run initial scrape:**
```bash
python run_scraper.py
```

6. **Extract route images (optional):**
```bash
python extract_ozcruising_images.py
```

7. **Start application:**
```bash
python app.py
# OR
uvicorn app:app --reload
```

## 🌐 Deployment

### **Deploy to Hetzner Cloud ($4.15/month):**

See [HETZNER_DEPLOYMENT.md](HETZNER_DEPLOYMENT.md) for detailed guide.

**Quick deploy:**
```bash
ssh root@YOUR_SERVER_IP
cd /var/www
git clone https://github.com/YOUR_USERNAME/cheapcruises.git
cd cheapcruises
./deployment/hetzner-quick-deploy.sh
```

### **Deploy to Render.com (Easy):**

1. Push to GitHub
2. Connect to Render.com
3. **Build:** `pip install -r requirements.txt`
4. **Start:** `uvicorn app:app --host 0.0.0.0 --port $PORT`

## 📊 API Endpoints

- `GET /api/deals` - Get all cruise deals (with filters)
- `GET /api/deals/best` - Get best deals by price threshold
- `GET /api/stats` - Get statistics
- `GET /api/promo-codes` - Get promo codes (if enabled)
- `GET /api/health` - Health check

**Full API docs:** http://localhost:8000/api/docs

## 🔄 How It Works

1. **Scraper** runs daily at 6 AM (configurable)
2. **Scrapes** 16 pages on OzCruising.com.au
3. **Extracts** cruise deals (ship, destination, price, dates)
4. **Saves** to SQLite database
5. **FastAPI** serves data via REST API
6. **Frontend** displays deals with filtering

## 📸 Route Map Images

Optional background job that extracts route map images:

```bash
python extract_ozcruising_images.py
```

This visits each cruise detail page and extracts the route map image.

**Time:** ~1-2 hours for all deals  
**Frequency:** Run weekly or as needed

## 🛠️ Configuration

Edit `.env` file:

```bash
DATABASE_URL=sqlite+aiosqlite:///./cruises.db
ENVIRONMENT=production
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
SCRAPER_SCHEDULE_HOUR=6
```

## 📝 License

MIT License - See LICENSE file

## 🤝 Contributing

Contributions welcome! This is a personal project showcasing web scraping and async Python.

## ⚠️ Disclaimer

This tool is for educational purposes. Always respect robots.txt and website terms of service. Cruise prices and availability should be verified on official cruise line websites.

## 📧 Support

For issues, see the documentation files:
- `DEPLOYMENT.md` - General deployment guide
- `HETZNER_DEPLOYMENT.md` - Hetzner-specific guide
- `QUICKSTART.md` - Local development guide

---

**Built with ❤️ for cruise enthusiasts**
