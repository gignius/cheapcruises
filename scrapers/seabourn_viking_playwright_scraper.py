"""Playwright DOM scrapers for Seabourn and Viking"""
import asyncio
from datetime import datetime
from typing import List
from playwright.async_api import async_playwright
import re
from models import CruiseDeal
from base_scraper import safe_print


class SeabournPlaywrightScraper:
    """Playwright scraper for Seabourn"""
    
    BASE_URL = "https://www.seabourn.com"
    SEARCH_URL = f"{BASE_URL}/en-us/find-a-cruise"
    
    @property
    def name(self) -> str:
        return "Seabourn (Playwright DOM)"

    def scrape(self) -> List[CruiseDeal]:
        import nest_asyncio
        nest_asyncio.apply()
        return asyncio.get_event_loop().run_until_complete(self._scrape_async())
    
    async def _scrape_async(self) -> List[CruiseDeal]:
        safe_print(f"\n🔍 Scraping {self.name}...")
        deals = []
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                
                await page.goto(self.SEARCH_URL, timeout=45000)
                await page.wait_for_timeout(6000)
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)
                
                # Extract any cruise-like content
                result = await page.evaluate("""() => {
                    const items = [];
                    document.querySelectorAll('*').forEach(el => {
                        const text = el.innerText || '';
                        if (text.match(/\\$\\d{3,}/) && text.match(/\\d+\\s*(?:night|day)/i) && text.length < 400) {
                            items.push({text, url: ''});
                        }
                    });
                    return items;
                }""")
                
                safe_print(f"  Found {len(result)} potential cruises")
                
                for item in result[:50]:  # Limit
                    deal = self._parse_generic(item, "Seabourn")
                    if deal and not self._is_duplicate(deals, deal):
                        deals.append(deal)
                
                await browser.close()
                
        except Exception as e:
            safe_print(f"⚠️  {self.name}: {e}")
        
        safe_print(f"✅ {self.name}: {len(deals)} deals")
        return deals
    
    def _parse_generic(self, item: dict, cruise_line: str) -> CruiseDeal:
        try:
            text = item.get('text', '')
            price_match = re.search(r'\$(\d{1,3}(?:,\d{3})*)', text)
            duration_match = re.search(r'(\d+)[- ](?:night|day)', text, re.I)
            
            if not price_match or not duration_match:
                return None
            
            price = float(price_match.group(1).replace(',', ''))
            duration = int(duration_match.group(1))
            duration_days = duration + 1 if 'night' in text.lower() else duration
            
            if price <= 0 or duration_days <= 0:
                return None
            
            return CruiseDeal(
                cruise_line=cruise_line,
                ship_name=f"{cruise_line} Ship",
                destination="Various",
                departure_date=datetime.now(),
                duration_days=duration_days,
                total_price_aud=price,
                price_per_day=price / duration_days,
                cabin_type="Interior",
                departure_port="Various",
                url=self.BASE_URL,
                scraped_at=datetime.now(),
                special_offers=None
            )
        except:
            return None
    
    def _is_duplicate(self, deals: List[CruiseDeal], new_deal: CruiseDeal) -> bool:
        for deal in deals:
            if (deal.duration_days == new_deal.duration_days and
                abs(deal.total_price_aud - new_deal.total_price_aud) < 10):
                return True
        return False


class VikingPlaywrightScraper:
    """Playwright scraper for Viking Ocean Cruises"""
    
    BASE_URL = "https://www.vikingcruises.com.au"
    SEARCH_URL = f"{BASE_URL}/cruise-destinations/index.html"
    
    @property
    def name(self) -> str:
        return "Viking Ocean Cruises (Playwright DOM)"

    def scrape(self) -> List[CruiseDeal]:
        import nest_asyncio
        nest_asyncio.apply()
        return asyncio.get_event_loop().run_until_complete(self._scrape_async())
    
    async def _scrape_async(self) -> List[CruiseDeal]:
        safe_print(f"\n🔍 Scraping {self.name}...")
        deals = []
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                
                await page.goto(self.SEARCH_URL, timeout=45000)
                await page.wait_for_timeout(6000)
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)
                
                result = await page.evaluate("""() => {
                    const items = [];
                    document.querySelectorAll('*').forEach(el => {
                        const text = el.innerText || '';
                        if (text.match(/\\$\\d{3,}/) && text.match(/\\d+\\s*(?:night|day)/i) && text.length < 400) {
                            items.push({text, url: ''});
                        }
                    });
                    return items;
                }""")
                
                safe_print(f"  Found {len(result)} potential cruises")
                
                for item in result[:50]:
                    deal = self._parse_generic(item)
                    if deal and not self._is_duplicate(deals, deal):
                        deals.append(deal)
                
                await browser.close()
                
        except Exception as e:
            safe_print(f"⚠️  {self.name}: {e}")
        
        safe_print(f"✅ {self.name}: {len(deals)} deals")
        return deals
    
    def _parse_generic(self, item: dict) -> CruiseDeal:
        try:
            text = item.get('text', '')
            price_match = re.search(r'\$(\d{1,3}(?:,\d{3})*)', text)
            duration_match = re.search(r'(\d+)[- ](?:night|day)', text, re.I)
            
            if not price_match or not duration_match:
                return None
            
            price = float(price_match.group(1).replace(',', ''))
            duration = int(duration_match.group(1))
            duration_days = duration + 1 if 'night' in text.lower() else duration
            
            if price <= 0 or duration_days <= 0:
                return None
            
            return CruiseDeal(
                cruise_line="Viking Ocean Cruises",
                ship_name="Viking Ship",
                destination="Various",
                departure_date=datetime.now(),
                duration_days=duration_days,
                total_price_aud=price,
                price_per_day=price / duration_days,
                cabin_type="Interior",
                departure_port="Various",
                url=self.BASE_URL,
                scraped_at=datetime.now(),
                special_offers=None
            )
        except:
            return None
    
    def _is_duplicate(self, deals: List[CruiseDeal], new_deal: CruiseDeal) -> bool:
        for deal in deals:
            if (deal.duration_days == new_deal.duration_days and
                abs(deal.total_price_aud - new_deal.total_price_aud) < 10):
                return True
        return False

