"""Playwright DOM scraper for Cunard"""
import asyncio
from datetime import datetime
from typing import List
from playwright.async_api import async_playwright
import re
from models import CruiseDeal
from base_scraper import safe_print


class CunardPlaywrightScraper:
    """Playwright scraper for Cunard (Carnival Corp brand)"""
    
    BASE_URL = "https://www.cunard.com"
    SEARCH_URL = f"{BASE_URL}/en-au/search"
    
    @property
    def name(self) -> str:
        return "Cunard (Playwright DOM)"

    def scrape(self) -> List[CruiseDeal]:
        import nest_asyncio
        nest_asyncio.apply()
        return asyncio.get_event_loop().run_until_complete(self._scrape_async())
    
    async def _scrape_async(self) -> List[CruiseDeal]:
        safe_print(f"\n🔍 Scraping {self.name} via browser DOM...")
        deals = []
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                
                safe_print(f"  Loading: {self.SEARCH_URL}")
                await page.goto(self.SEARCH_URL, wait_until='domcontentloaded', timeout=60000)
                await page.wait_for_timeout(10000)
                
                # Scroll and wait
                for _ in range(3):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(2000)
                
                # Extract via JavaScript
                result = await page.evaluate("""() => {
                    const cruises = [];
                    const elements = document.querySelectorAll('[class*="cruise"], [class*="voyage"], [class*="sailing"], article, .card');
                    
                    elements.forEach(el => {
                        const text = el.innerText || '';
                        if (text.match(/\\$\\d{3,}/) && (text.match(/night/i) || text.match(/day/i))) {
                            const links = el.querySelectorAll('a[href]');
                            const url = links.length > 0 ? links[0].href : '';
                            cruises.push({text, url});
                        }
                    });
                    
                    return cruises;
                }""")
                
                safe_print(f"  Found {len(result)} potential cruises")
                
                for item in result:
                    deal = self._parse_item(item)
                    if deal and not self._is_duplicate(deals, deal):
                        deals.append(deal)
                
                safe_print(f"✅ Successfully scraped {len(deals)} deals from {self.name}")
                await browser.close()
                
        except Exception as e:
            safe_print(f"❌ Error: {e}")
        
        return deals
    
    def _parse_item(self, item: dict) -> CruiseDeal:
        """Parse cruise from DOM item"""
        try:
            text = item.get('text', '')
            url = item.get('url', self.BASE_URL)
            
            # Extract price
            price_match = re.search(r'\$(\d{1,3}(?:,\d{3})*)', text)
            if not price_match:
                return None
            price = float(price_match.group(1).replace(',', ''))
            
            # Extract duration
            duration_match = re.search(r'(\d+)[- ](?:night|day)', text, re.I)
            if not duration_match:
                return None
            duration = int(duration_match.group(1))
            duration_days = duration + 1 if 'night' in text.lower() else duration
            
            # Extract ship (Queen Mary 2, Queen Elizabeth, Queen Victoria, Queen Anne)
            ship_patterns = [r'(Queen (?:Mary 2|Elizabeth|Victoria|Anne))']
            ship_name = "Cunard Ship"
            for pattern in ship_patterns:
                ship_match = re.search(pattern, text, re.I)
                if ship_match:
                    ship_name = ship_match.group(1)
                    break
            
            # Extract destination
            dest_match = re.search(r'(Caribbean|Mediterranean|Transatlantic|Europe|World Cruise|Alaska|Asia|Australia)', text, re.I)
            destination = dest_match.group(1) if dest_match else "Various"
            
            price_per_day = price / duration_days if duration_days > 0 else float('inf')
            
            if price <= 0 or duration_days <= 0:
                return None
            
            return CruiseDeal(
                cruise_line="Cunard",
                ship_name=ship_name,
                destination=destination,
                departure_date=datetime.now(),
                duration_days=duration_days,
                total_price_aud=price,
                price_per_day=price_per_day,
                cabin_type="Interior",
                departure_port="Various",
                url=url if url and url.startswith('http') else self.BASE_URL,
                scraped_at=datetime.now(),
                special_offers=None
            )
        except:
            return None
    
    def _is_duplicate(self, deals: List[CruiseDeal], new_deal: CruiseDeal) -> bool:
        for deal in deals:
            if (deal.ship_name == new_deal.ship_name and
                deal.destination == new_deal.destination and
                deal.duration_days == new_deal.duration_days and
                abs(deal.total_price_aud - new_deal.total_price_aud) < 10):
                return True
        return False

