"""Playwright-based scraper for Carnival Cruise Line Australia"""
import re
import asyncio
from datetime import datetime
from typing import List
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
from models import CruiseDeal
from base_scraper import safe_print


class CarnivalScraperPlaywright:
    """Playwright scraper for Carnival Cruise Line Australia website"""
    
    BASE_URL = "https://www.carnival.com.au"
    DEALS_URL = f"{BASE_URL}/cruise-deals"
    
    @property
    def name(self) -> str:
        return "Carnival Australia (Browser)"

    def scrape(self) -> List[CruiseDeal]:
        """Scrape cruise deals from Carnival using Playwright"""
        # Run the async scraper in a new event loop to avoid conflicts
        import nest_asyncio
        nest_asyncio.apply()
        return asyncio.get_event_loop().run_until_complete(self._scrape_async())
    
    async def _scrape_async(self) -> List[CruiseDeal]:
        """Async scraping method"""
        safe_print(f"\n🔍 Scraping {self.name} with browser automation...")
        deals = []
        
        try:
            async with async_playwright() as p:
                # Launch browser with realistic settings
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--disable-blink-features=AutomationControlled']
                )
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                    locale='en-AU',
                    timezone_id='Australia/Sydney'
                )
                
                # Add extra headers
                await context.set_extra_http_headers({
                    'Accept-Language': 'en-AU,en;q=0.9',
                })
                
                page = await context.new_page()
                
                safe_print(f"  Loading: {self.DEALS_URL}")
                
                # Load page with timeout
                try:
                    await page.goto(self.DEALS_URL, wait_until='domcontentloaded', timeout=45000)
                    # Wait a bit for JavaScript to execute
                    await page.wait_for_timeout(3000)
                except PlaywrightTimeout:
                    safe_print(f"  ⚠️  Page load timeout, trying to parse what we have...")
                
                # Scroll to trigger lazy loading
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)
                
                # Get page content
                content = await page.content()
                safe_print(f"  Page loaded: {len(content)} bytes")
                
                # Parse with BeautifulSoup
                soup = BeautifulSoup(content, 'lxml')
                
                # Look for deal links in the HTML
                deal_links = soup.find_all('a', href=re.compile(r'/cruises/|/itinerary/', re.I))
                safe_print(f"  Found {len(deal_links)} potential cruise links")
                
                # Try to extract deals from various selectors
                price_elements = soup.find_all(string=re.compile(r'\$\d{3,}'))
                safe_print(f"  Found {len(price_elements)} price indicators")
                
                # Look for structured data or JSON
                scripts = soup.find_all('script', type='application/ld+json')
                for script in scripts:
                    try:
                        import json
                        data = json.loads(script.string)
                        if isinstance(data, dict) and data.get('@type') in ['Product', 'Offer']:
                            deal = self._parse_json_deal(data)
                            if deal:
                                deals.append(deal)
                    except:
                        pass
                
                safe_print(f"✅ Successfully scraped {len(deals)} deals from {self.name}")
                
                await browser.close()
                
        except Exception as e:
            safe_print(f"❌ Error scraping {self.name}: {e}")
            import traceback
            traceback.print_exc()
        
        return deals
    
    def _parse_json_deal(self, data: dict) -> CruiseDeal:
        """Parse deal from JSON-LD data"""
        try:
            offers = data.get('offers', {})
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            
            price = float(offers.get('price', 0))
            name = data.get('name', '')
            
            # Extract duration
            duration_match = re.search(r'(\d+)\s*(?:Night|Day)', name, re.I)
            duration = int(duration_match.group(1)) + 1 if duration_match else 7
            
            if price and duration:
                return CruiseDeal(
                    cruise_line="Carnival",
                    ship_name=name.split('-')[0].strip() if '-' in name else "Carnival Ship",
                    destination=name.split('-')[1].strip() if '-' in name else "Various",
                    departure_date=datetime.now(),
                    duration_days=duration,
                    total_price_aud=price,
                    price_per_day=price / duration,
                    cabin_type="Interior",
                    departure_port="Various Ports",
                    url=data.get('url', self.DEALS_URL),
                    scraped_at=datetime.now(),
                    special_offers=offers.get('description', '')
                )
        except:
            pass
        return None

