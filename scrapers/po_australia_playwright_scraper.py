"""Playwright DOM scraper for P&O Australia"""
import asyncio
from datetime import datetime
from typing import List
from playwright.async_api import async_playwright
import re
from models import CruiseDeal
from base_scraper import safe_print


class POAustraliaPlaywrightScraper:
    """Playwright scraper for P&O Australia"""
    
    BASE_URL = "https://www.pocruises.com.au"
    SEARCH_URL = f"{BASE_URL}/search"
    
    @property
    def name(self) -> str:
        return "P&O Australia (Playwright DOM)"

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
                await page.wait_for_timeout(8000)
                
                for _ in range(3):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(2000)
                
                result = await page.evaluate("""() => {
                    const cruises = [];
                    document.querySelectorAll('*').forEach(el => {
                        const text = el.innerText || '';
                        if (text.match(/\\$\\d{3,}/) && text.match(/\\d+\\s*night/i) && text.length < 500) {
                            const links = el.querySelectorAll('a[href]');
                            cruises.push({
                                text,
                                url: links.length > 0 ? links[0].href : ''
                            });
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
        try:
            text = item.get('text', '')
            url = item.get('url', self.BASE_URL)
            
            price_match = re.search(r'\$(\d{1,3}(?:,\d{3})*)', text)
            if not price_match:
                return None
            price = float(price_match.group(1).replace(',', ''))
            
            duration_match = re.search(r'(\d+)[- ](?:night|day)', text, re.I)
            if not duration_match:
                return None
            duration = int(duration_match.group(1))
            duration_days = duration + 1 if 'night' in text.lower() else duration
            
            # P&O ships: Pacific Explorer, Pacific Adventure, Pacific Encounter
            ship_match = re.search(r'(Pacific (?:Explorer|Adventure|Encounter))', text, re.I)
            ship_name = ship_match.group(1) if ship_match else "P&O Ship"
            
            dest_match = re.search(r'(Queensland|New Zealand|South Pacific|Fiji|Vanuatu|New Caledonia|Tasmania)', text, re.I)
            destination = dest_match.group(1) if dest_match else "Various"
            
            price_per_day = price / duration_days if duration_days > 0 else float('inf')
            
            if price <= 0 or duration_days <= 0:
                return None
            
            return CruiseDeal(
                cruise_line="P&O Australia",
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

