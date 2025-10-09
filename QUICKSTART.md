# 🚀 Quick Start Guide

Get up and running in 3 minutes!

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Run the Scraper

```bash
python main.py
```

That's it! The scraper will:
- Search Royal Caribbean, Carnival, and OzCruising
- Find deals under $100/day AUD
- Display results in your console

## Step 3: Optional - Enable Email Alerts

Create a file named `.env` in the project folder:

```
EMAIL_ENABLED=true
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password
RECIPIENT_EMAIL=where_to_send@example.com
```

Then run with email:
```bash
python main.py --email
```

## Common Commands

**Find cheaper deals (under $80/day):**
```bash
python main.py --threshold 80
```

**Save results to a file:**
```bash
python main.py --save
```

**Run only OzCruising scraper:**
```bash
python main.py --scrapers ozcruising
```

**Do everything:**
```bash
python main.py --threshold 100 --email --save
```

## What to Expect

The scraper will:
1. Visit each cruise website
2. Extract deal information
3. Calculate price per day
4. Show you the best deals!

**Example Output:**
```
🚢 CRUISE DEAL SCRAPER 🚢
================================================================================
Started at: 2025-10-08 10:30:00
Price threshold: $100/day AUD
================================================================================

🔍 Scraping OzCruising.com.au...
📦 Found 25 potential deals
✅ Successfully scraped 25 deals from OzCruising.com.au
  └─ OzCruising.com.au: 25 total deals, 5 under $100/day

🔍 Scraping Royal Caribbean...
📦 Found 18 potential deals
✅ Successfully scraped 18 deals from Royal Caribbean
  └─ Royal Caribbean: 18 total deals, 3 under $100/day

🔍 Scraping Carnival Cruise Line...
📦 Found 15 potential deals
✅ Successfully scraped 15 deals from Carnival Cruise Line
  └─ Carnival Cruise Line: 15 total deals, 2 under $100/day

================================================================================
📊 SUMMARY
================================================================================
Total deals scraped: 58
Deals under $100/day: 10
================================================================================

🎉 FOUND 10 AMAZING CRUISE DEAL(S) UNDER $100/DAY! 🎉
```

## Troubleshooting

**"No module named 'requests'"**
- Run: `pip install -r requirements.txt`

**"No deals found"**
- Try a higher threshold: `python main.py --threshold 150`
- Websites may have changed - this is normal for web scrapers
- Check back later or try individual scrapers

**Need help?**
- Check the full README.md for detailed documentation
- Make sure you're in the project directory when running commands

---

**Happy cruise hunting! ⛵**

