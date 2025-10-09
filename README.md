# 🚢 CheapCruises.io

**Find the best cruise deals in Australia - automated scraping, filtering, and promo code tracking.**

---

## Features

✅ **Automated Scraping** - Daily scraping of major cruise websites  
✅ **Price Filtering** - Find deals under $100, $150, $200 per night  
✅ **Advanced Search** - Filter by cruise line, port, duration  
✅ **Promo Codes** - Verified promo codes from official sources  
✅ **Production-Ready** - FastAPI + PostgreSQL + SQLAlchemy async  
✅ **Beautiful UI** - Alpine.js + Tailwind CSS  
✅ **RESTful API** - Full API with automatic documentation  

---

## Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with SQLAlchemy 2.0 (async)
- **Frontend**: Jinja2 templates + Alpine.js + Tailwind CSS
- **Jobs**: APScheduler for background scraping
- **Web Server**: Uvicorn + Nginx
- **Process Manager**: Systemd

---

## Quick Start (Development)

### 1. Clone and Setup

```bash
git clone <repo-url>
cd Cheapcruises
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

For development, you can use SQLite:
```env
DATABASE_URL=sqlite+aiosqlite:///./cruises.db
```

### 3. Initialize Database

```python
python -c "import asyncio; from database_async import init_db; asyncio.run(init_db())"
```

### 4. Run Development Server

```bash
python app.py
```

Or with uvicorn:
```bash
uvicorn app:app --reload
```

Visit:
- **Website**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs
- **Health Check**: http://localhost:8000/api/health

---

## Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete production deployment guide for Hetzner servers.

**Quick Deploy:**
```bash
sudo bash deployment/setup.sh
```

---

## Manual Scraper Run

Run scrapers manually:
```bash
python run_scraper.py
```

Or via API:
```bash
curl -X POST http://localhost:8000/api/admin/run-scrapers
```

---

## API Endpoints

### Cruise Deals

- `GET /api/deals` - List all deals with filters
  - Query params: `max_price_per_day`, `cruise_line`, `departure_port`, `min_duration`, `max_duration`, `sort_by`, `order`
- `GET /api/deals/best` - Best deals under $100/$150/$200
- `GET /api/stats` - Statistics about deals

### Promo Codes

- `GET /api/promo-codes` - List promo codes
  - Query params: `cruise_line`, `valid_only`

### System

- `GET /api/health` - Health check
- `GET /api/docs` - Interactive API documentation
- `GET /api/redoc` - Alternative API documentation

---

## Project Structure

```
Cheapcruises/
├── app.py                    # Main FastAPI application
├── config_settings.py        # Pydantic settings
├── database_async.py         # Async database layer
├── db_models.py             # SQLAlchemy models
├── models.py                # Pydantic models
├── promo_codes.py           # Promo code management
├── promo_code_scraper.py    # Promo code scraping
├── scheduler.py             # Background job scheduler
├── run_scraper.py           # Manual scraper runner
├── scrapers/                # Cruise website scrapers
│   ├── __init__.py
│   ├── ozcruising_scraper.py
│   ├── royal_caribbean_scraper.py
│   └── carnival_scraper.py
├── templates/               # Jinja2 templates
│   ├── base.html
│   ├── index.html
│   ├── deals.html
│   └── promo_codes.html
├── static/                  # Static files (CSS/JS)
├── deployment/              # Deployment configs
│   ├── nginx/
│   ├── systemd/
│   └── setup.sh
├── requirements.txt
├── .env.example
├── README.md
└── DEPLOYMENT.md
```

---

## Configuration

All configuration via environment variables in `.env`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/cruises

# Scraping
PRICE_THRESHOLD=200.0
SCRAPER_SCHEDULE_HOUR=6  # Run at 6 AM daily

# Server
PORT=8000
WORKERS=4
DEBUG=False
```

---

## Scraper Schedule

Scrapers run automatically via APScheduler:
- **Cruise Deals**: Daily at 6:00 AM
- **Promo Codes**: Daily at 12:30 AM

To change schedule, edit `config_settings.py`:
```python
scraper_schedule_hour: int = 6
```

---

## Adding New Scrapers

1. Create new scraper in `scrapers/` directory
2. Extend `BaseScraper` class
3. Implement `scrape()` method
4. Add to `scheduler.py`

Example:
```python
from base_scraper import BaseScraper

class NewScraper(BaseScraper):
    @property
    def name(self) -> str:
        return "New Cruise Site"
    
    def scrape(self) -> List[CruiseDeal]:
        # Your scraping logic
        pass
```

---

## Database Management

### Migrations

The app auto-creates tables on startup. For production migrations:

```bash
# Install Alembic (already in requirements.txt)
alembic init migrations
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### Backup

```bash
# Backup
pg_dump cruises > backup.sql

# Restore
psql cruises < backup.sql
```

---

## Monitoring

### Application Logs

```bash
# Development
# Logs print to console

# Production (systemd)
sudo journalctl -u cheapcruises -f
```

### Database Queries

```bash
# Connect to database
psql -U cruises -d cruises

# Count deals
SELECT COUNT(*) FROM cruise_deals WHERE is_active = true;

# Best deals
SELECT cruise_line, ship_name, price_per_day 
FROM cruise_deals 
WHERE is_active = true 
ORDER BY price_per_day 
LIMIT 10;
```

---

## Development

### Run Tests

```bash
pytest
```

### Code Quality

```bash
# Format code
black .

# Lint
flake8 .

# Type checking
mypy .
```

---

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `DEBUG` | Debug mode | False |
| `PRICE_THRESHOLD` | Price threshold per night | 200.0 |
| `PORT` | Server port | 8000 |
| `WORKERS` | Uvicorn workers | 4 |
| `SCRAPER_SCHEDULE_HOUR` | Hour to run scrapers (0-23) | 6 |
| `SECRET_KEY` | App secret key | Generate with openssl |

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000
# Kill it
kill -9 <PID>
```

### Database Connection Error

```bash
# Check PostgreSQL is running
systemctl status postgresql

# Test connection
psql -U cruises -d cruises -c "SELECT 1;"
```

### Scraper Not Finding Deals

1. Check if website structure changed
2. View scraper logs
3. Test scraper manually:
   ```python
   from scrapers import OzCruisingScraper
   scraper = OzCruisingScraper()
   deals = scraper.scrape()
   print(f"Found {len(deals)} deals")
   ```

---

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## License

MIT License - see LICENSE file for details

---

## Roadmap

- [ ] Add more cruise line scrapers
- [ ] Email alerts for new deals
- [ ] Price history tracking
- [ ] User accounts and watchlists
- [ ] Mobile app (React Native)
- [ ] Booking integration

---

## Support

- **Documentation**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **API Docs**: http://localhost:8000/api/docs
- **Issues**: GitHub Issues

---

## Acknowledgments

- FastAPI for amazing async framework
- Beautiful Soup for web scraping
- Tailwind CSS for styling
- Alpine.js for interactivity

---

**Happy Cruising! 🚢⚓**
