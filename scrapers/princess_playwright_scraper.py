"""Playwright DOM scraper for Princess Cruises"""
import asyncio
from datetime import datetime
from typing import List
from playwright.async_api import async_playwright
import re
from models import CruiseDeal
from base_scraper import safe_print


class PrincessPlaywrightScraper:
    """Playwright scraper that extracts cruise data from rendered DOM"""
    
    BASE_URL = "https://www.princess.com"
    SEARCH_URL = "https://book.princess.com/bookCruise/cruiseSearch/?voyageType=C"
    
    @property
    def name(self) -> str:
        return "Princess Cruises (Playwright DOM)"

    def scrape(self) -> List[CruiseDeal]:
        """Scrape by executing JavaScript and reading rendered DOM"""
        import nest_asyncio
        nest_asyncio.apply()
        return asyncio.get_event_loop().run_until_complete(self._scrape_async())
    
    async def _scrape_async(self) -> List[CruiseDeal]:
        safe_print(f"\n🔍 Scraping {self.name} via browser DOM extraction...")
        deals = []
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    viewport={'width': 1920, 'height': 1080}
                )
                
                page = await context.new_page()
                
                safe_print(f"  Loading: {self.SEARCH_URL}")
                await page.goto(self.SEARCH_URL, wait_until='networkidle', timeout=60000)
                
                # Wait for cruise results to render
                await page.wait_for_timeout(8000)
                
                # Scroll to load all results
                for _ in range(3):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(2000)
                
                # Extract cruise cards from DOM
                safe_print(f"  Extracting cruise data from DOM...")
                
                # Try multiple selectors for cruise cards
                selectors = [
                    '.cruise-card',
                    '[class*="cruise"]',
                    '[class*="voyage"]',
                    '[class*="sailing"]',
                    'article',
                    '.search-result',
                ]
                
                cruise_elements = []
                for selector in selectors:
                    elements = await page.query_selector_all(selector)
                    if elements and len(elements) > 5:  # Found substantial results
                        cruise_elements = elements
                        safe_print(f"  Found {len(elements)} elements with selector: {selector}")
                        break
                
                if not cruise_elements:
                    # Extract via JavaScript evaluation
                    safe_print(f"  No elements found, trying JavaScript extraction...")
                    result = await page.evaluate("""() => {
                        const results = [];
                        // Look for price elements
                        const prices = Array.from(document.querySelectorAll('*')).filter(el => 
                            el.textContent && el.textContent.match(/\\$\\d{3,}/)
                        );
                        
                        // Get parent containers
                        const containers = new Set();
                        prices.forEach(price => {
                            let parent = price;
                            for (let i = 0; i < 10; i++) {
                                parent = parent.parentElement;
                                if (!parent) break;
                                if (parent.textContent.includes('night') || parent.textContent.includes('day')) {
                                    containers.add(parent);
                                    break;
                                }
                            }
                        });
                        
                        containers.forEach(container => {
                            results.push({
                                text: container.innerText,
                                html: container.outerHTML.substring(0, 500)
                            });
                        });
                        
                        return results;
                    }""")
                    
                    safe_print(f"  Found {len(result)} potential cruise containers via JS")
                    
                    # Parse the extracted data
                    for item in result:
                        deal = self._parse_text_content(item['text'])
                        if deal:
                            deals.append(deal)
                
                else:
                    # Parse found elements
                    for element in cruise_elements[:100]:  # Limit to 100
                        try:
                            text = await element.inner_text()
                            html = await element.inner_html()
                            deal = self._parse_element(text, html, element)
                            if deal and not self._is_duplicate(deals, deal):
                                deals.append(deal)
                        except:
                            continue
                
                safe_print(f"✅ Successfully scraped {len(deals)} deals from {self.name}")
                await browser.close()
                
        except Exception as e:
            safe_print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        return deals
    
    async def _parse_element(self, text: str, html: str, element) -> CruiseDeal:
        """Parse cruise data from element"""
        try:
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
            
            # Extract ship name
            ship_patterns = [
                r'(Crown Princess|Diamond Princess|Discovery Princess|Enchanted Princess|Grand Princess|Island Princess|Majestic Princess|Royal Princess|Regal Princess|Ruby Princess|Sapphire Princess|Sky Princess|Sun Princess)',
            ]
            ship_name = "Princess Ship"
            for pattern in ship_patterns:
                ship_match = re.search(pattern, text, re.I)
                if ship_match:
                    ship_name = ship_match.group(1)
                    break
            
            # Extract destination
            dest_patterns = [
                r'(Caribbean|Alaska|Europe|Mexico|Hawaii|Panama|Asia|Australia|South Pacific|Mediterranean|Transatlantic|Scandinavia)',
            ]
            destination = "Various"
            for pattern in dest_patterns:
                dest_match = re.search(pattern, text, re.I)
                if dest_match:
                    destination = dest_match.group(1)
                    break
            
            # Extract URL
            url = await element.query_selector('a[href]')
            url_str = await url.get_attribute('href') if url else ""
            if url_str:
                if not url_str.startswith('http'):
                    url_str = f"{self.BASE_URL}{url_str}"
            else:
                url_str = self.BASE_URL
            
            price_per_day = price / duration_days if duration_days > 0 else float('inf')
            
            if price <= 0 or duration_days <= 0:
                return None
            
            return CruiseDeal(
                cruise_line="Princess Cruises",
                ship_name=ship_name,
                destination=destination,
                departure_date=datetime.now(),
                duration_days=duration_days,
                total_price_aud=price,
                price_per_day=price_per_day,
                cabin_type="Interior",
                departure_port="Various",
                url=url_str,
                scraped_at=datetime.now(),
                special_offers=None
            )
            
        except Exception as e:
            return None
    
    def _parse_text_content(self, text: str) -> CruiseDeal:
        """Parse cruise from text content"""
        # Similar parsing logic
        try:
            price_match = re.search(r'\$(\d{1,3}(?:,\d{3})*)', text)
            if not price_match:
                return None
            price = float(price_match.group(1).replace(',', ''))
            
            duration_match = re.search(r'(\d+)[- ](?:night|day)', text, re.I)
            if not duration_match:
                return None
            duration = int(duration_match.group(1))
            duration_days = duration + 1 if 'night' in text.lower() else duration
            
            if price <= 0 or duration_days <= 0:
                return None
            
            return CruiseDeal(
                cruise_line="Princess Cruises",
                ship_name="Princess Ship",
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
            if (deal.ship_name == new_deal.ship_name and
                deal.destination == new_deal.destination and
                deal.duration_days == new_deal.duration_days and
                abs(deal.total_price_aud - new_deal.total_price_aud) < 10):
                return True
        return False

