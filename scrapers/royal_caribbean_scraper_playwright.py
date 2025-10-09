"""Playwright-based scraper for Royal Caribbean Australia"""
import re
import asyncio
from datetime import datetime
from typing import List
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
from models import CruiseDeal
from base_scraper import safe_print


class RoyalCaribbeanScraperPlaywright:
    """Playwright scraper for Royal Caribbean Australia website"""
    
    BASE_URL = "https://www.royalcaribbean.com.au"
    DEALS_URL = f"{BASE_URL}/aus/en/cruise-deals"
    
    @property
    def name(self) -> str:
        return "Royal Caribbean Australia (Browser)"

    def scrape(self) -> List[CruiseDeal]:
        """Scrape cruise deals from Royal Caribbean using Playwright"""
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
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                    ]
                )
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                    locale='en-AU',
                    timezone_id='Australia/Sydney'
                )
                
                await context.set_extra_http_headers({
                    'Accept-Language': 'en-AU,en;q=0.9',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                })
                
                page = await context.new_page()
                
                safe_print(f"  Loading: {self.DEALS_URL}")
                
                # Try to load page - Royal Caribbean can be slow
                try:
                    response = await page.goto(self.DEALS_URL, wait_until='domcontentloaded', timeout=60000)
                    safe_print(f"  Response status: {response.status if response else 'No response'}")
                    
                    # Wait for content to load
                    await page.wait_for_timeout(5000)
                    
                    # Try to wait for specific selectors
                    try:
                        await page.wait_for_selector('body', timeout=10000)
                    except:
                        pass
                        
                except PlaywrightTimeout:
                    safe_print(f"  ⚠️  Timeout loading page - will try to parse anyway...")
                except Exception as e:
                    safe_print(f"  ⚠️  Error loading page: {e}")
                    await browser.close()
                    return deals
                
                # Scroll to trigger lazy loading
                try:
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(3000)
                except:
                    pass
                
                # Get page content
                content = await page.content()
                safe_print(f"  Page loaded: {len(content)} bytes")
                
                # Parse with BeautifulSoup
                soup = BeautifulSoup(content, 'lxml')
                
                # Look for cruise/deal links
                deal_links = soup.find_all('a', href=re.compile(r'/cruises/|/cruise-search/|/booking/', re.I))
                safe_print(f"  Found {len(deal_links)} potential cruise links")
                
                # Look for price indicators
                price_elements = soup.find_all(string=re.compile(r'\$\d{3,}|AUD\s*\d{3,}'))
                safe_print(f"  Found {len(price_elements)} price indicators")
                
                # Look for structured data
                scripts = soup.find_all('script', type='application/ld+json')
                safe_print(f"  Found {len(scripts)} JSON-LD scripts")
                
                for script in scripts:
                    try:
                        import json
                        data = json.loads(script.string)
                        if isinstance(data, list):
                            for item in data:
                                deal = self._parse_json_deal(item)
                                if deal:
                                    deals.append(deal)
                        elif isinstance(data, dict):
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
            if data.get('@type') not in ['Product', 'Offer', 'Trip']:
                return None
                
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
                    cruise_line="Royal Caribbean",
                    ship_name=name.split('-')[0].strip() if '-' in name else "Royal Caribbean Ship",
                    destination=name.split('-')[1].strip() if '-' in name else "Various",
                    departure_date=datetime.now(),
                    duration_days=duration,
                    total_price_aud=price,
                    price_per_day=price / duration,
                    cabin_type="Interior",
                    departure_port="Various Ports",
                    url=data.get('url', self.DEALS_URL),
                    scraped_at=datetime.now(),
                    special_offers=data.get('description', '')
                )
        except:
            pass
        return None

