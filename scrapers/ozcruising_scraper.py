"""Scraper for ozcruising.com.au"""
import re
from datetime import datetime
from typing import List, Optional
from base_scraper import BaseScraper
from models import CruiseDeal
from loguru import logger


class OzCruisingScraper(BaseScraper):
    """Scraper for OzCruising website"""
    
    BASE_URL = "https://www.ozcruising.com.au"
    SEARCH_URL = f"{BASE_URL}/deals"
    
    @property
    def name(self) -> str:
        return "OzCruising.com.au"

    def scrape(self) -> List[CruiseDeal]:
        """Scrape cruise deals from OzCruising"""
        logger.info(f"Starting scrape of {self.name}")
        self.deals = []
        
        try:
            # Scrape multiple pages for more deals - EXPANDED COVERAGE
            pages_to_scrape = [
                # Homepage & Specials
                self.BASE_URL,  # Homepage featured deals
                f"{self.BASE_URL}/cruise-specials",  # Special deals
                f"{self.BASE_URL}/last-minute-cruises",  # Last minute deals
                f"{self.BASE_URL}/deals",  # Main deals page
                
                # Australian Ports (expanded)
                f"{self.BASE_URL}/cheap-cruises-from-sydney",
                f"{self.BASE_URL}/cheap-cruises-from-brisbane",
                f"{self.BASE_URL}/cheap-cruises-from-melbourne",
                f"{self.BASE_URL}/cheap-cruises-from-perth",
                f"{self.BASE_URL}/cheap-cruises-from-adelaide",
                f"{self.BASE_URL}/cheap-cruises-from-fremantle",
                f"{self.BASE_URL}/cheap-cruises-from-hobart",
                f"{self.BASE_URL}/cheap-cruises-from-darwin",
                
                # International Ports (expanded)
                f"{self.BASE_URL}/cheap-cruises-from-auckland",
                f"{self.BASE_URL}/cheap-cruises-from-singapore",
                f"{self.BASE_URL}/cheap-cruises-from-hong-kong",
                f"{self.BASE_URL}/cheap-cruises-from-tokyo",
                f"{self.BASE_URL}/cheap-cruises-from-vancouver",
                f"{self.BASE_URL}/cheap-cruises-from-miami",
                f"{self.BASE_URL}/cheap-cruises-from-southampton",
                f"{self.BASE_URL}/cheap-cruises-from-rome",
                f"{self.BASE_URL}/cheap-cruises-from-barcelona",
                
                # All Cruise Lines (comprehensive)
                f"{self.BASE_URL}/searchcruise/bysearchbar/17/-111/-111/-111/true/-111/-111/-111/-111",  # Carnival
                f"{self.BASE_URL}/searchcruise/bysearchbar/5/-111/-111/-111/true/-111/-111/-111/-111/all-bold",  # Royal Caribbean
                f"{self.BASE_URL}/searchcruise/bysearchbar/4/-111/-111/-111/true/-111/-111/-111/-111-bold",  # Princess
                f"{self.BASE_URL}/searchcruise/bysearchbar/26/-111/-111/-111/true/-111/-111/-111/-111-bold",  # Norwegian
                f"{self.BASE_URL}/searchcruise/bysearchbar/1/-111/-111/-111/true/-111/-111/-111/-111-bold",  # Celebrity
                f"{self.BASE_URL}/searchcruise/bysearchbar/2/-111/-111/-111/true/-111/-111/-111/-111-bold",  # Holland America
                f"{self.BASE_URL}/searchcruise/bysearchbar/6/-111/-111/-111/true/-111/-111/-111/-111-bold",  # Cunard
                f"{self.BASE_URL}/searchcruise/bysearchbar/3/-111/-111/-111/true/-111/-111/-111/-111-bold",  # P&O Australia
                f"{self.BASE_URL}/searchcruise/bysearchbar/20/-111/-111/-111/false/-111/-111/-111/-111/all/-111-bold",  # MSC
                f"{self.BASE_URL}/searchcruise/bysearchbar/18/-111/-111/-111/true/-111/-111/-111/-111/all/-111-bold",  # Seabourn
                f"{self.BASE_URL}/searchcruise/bysearchbar/47/-111/-111/-111/true/-111/-111/-111/-111/all/-111-bold",  # Viking
                f"{self.BASE_URL}/searchcruise/bysearchbar/azamaraclubcruises/-111/-111/-111/false/-111/-111/-111/-111/-111/-111-bold",  # Azamara
                f"{self.BASE_URL}/searchcruise/bysearchbar/silversea-cruises/-111/-111/-111/false/-111/-111/-111/-111/-111/-111-bold",  # Silversea
                f"{self.BASE_URL}/searchcruise/bysearchbar/oceania-cruises/-111/-111/-111/false/-111/-111/-111/-111/-111/-111-bold",  # Oceania
                
                # Popular Destinations (worldwide coverage - expanded)
                f"{self.BASE_URL}/caribbean-cruises",
                f"{self.BASE_URL}/alaska-cruises",
                f"{self.BASE_URL}/mediterranean-cruises",
                f"{self.BASE_URL}/europe-cruises",
                f"{self.BASE_URL}/south-pacific-cruises",
                f"{self.BASE_URL}/asia-cruises",
                f"{self.BASE_URL}/new-zealand-cruises",
                f"{self.BASE_URL}/hawaii-cruises",
                f"{self.BASE_URL}/transatlantic-cruises",
                f"{self.BASE_URL}/world-cruises",
                f"{self.BASE_URL}/australia-cruises",
                f"{self.BASE_URL}/scandinavia-cruises",
                f"{self.BASE_URL}/canada-cruises",
            ]
            
            # Scrape simple pages (homepage, specials, ports)
            simple_pages = pages_to_scrape[:22]  # First 22 are non-paginated (homepage, specials, ports)
            for page_url in simple_pages:
                logger.debug(f"Scraping: {page_url}")
                soup = self.get_page(page_url)
                if soup:
                    self._parse_page(soup)
            
            # Scrape cruise line pages WITH PAGINATION (get ALL deals!)
            cruise_line_pages = pages_to_scrape[22:36]  # Cruise line search pages
            for page_url in cruise_line_pages:
                logger.debug(f"Scraping with pagination: {page_url}")
                self._scrape_with_pagination(page_url, max_pages=5)  # Increased to 5 pages for more coverage
            
            # Scrape destination pages
            destination_pages = pages_to_scrape[36:]  # Remaining are destinations
            for page_url in destination_pages:
                logger.debug(f"Scraping: {page_url}")
                soup = self.get_page(page_url)
                if soup:
                    self._parse_page(soup)
            
            logger.info(f"Enriching {len(self.deals)} deals with images from detail pages...")
            self._enrich_deals_with_images()
            
            logger.success(f"Successfully scraped {len(self.deals)} deals from {self.name}")
            
        except Exception as e:
            logger.error(f"Error scraping {self.name}: {e}", exc_info=True)
        
        return self.deals
    
    def _scrape_with_pagination(self, base_url: str, max_pages: int = 100):
        """Scrape a URL with pagination support"""
        page_num = 1
        consecutive_empty_pages = 0
        
        while page_num <= max_pages:
            # Construct paginated URL
            if '?' in base_url:
                url = f"{base_url}&page={page_num}"
            else:
                url = f"{base_url}?page={page_num}"
            
            logger.debug(f"Page {page_num}: {url[:80]}...")
            soup = self.get_page(url)
            
            if not soup:
                logger.warning(f"Failed to fetch page {page_num}")
                break
            
            # Count cruise details links on this page (before deduplication)
            cruise_links_on_page = soup.find_all('a', string=re.compile(r'View\s+Cruise\s+Details', re.I))
            
            if len(cruise_links_on_page) == 0:
                # No cruises at all on this page
                consecutive_empty_pages += 1
                if consecutive_empty_pages >= 2:
                    logger.debug(f"Stopping pagination after {consecutive_empty_pages} empty pages")
                    break
                page_num += 1
                continue
            
            # Parse this page
            deals_before = len(self.deals)
            self._parse_page(soup)
            deals_found = len(self.deals) - deals_before
            
            logger.debug(f"Page {page_num}: {len(cruise_links_on_page)} cruises found, {deals_found} new deals after dedup")
            
            # Continue even if we didn't find new deals (might be duplicates, but next page might have new ones)
            consecutive_empty_pages = 0
            page_num += 1
    
    def _parse_page(self, soup):
        """Parse a single page for deals"""
        try:
            # OzCruising displays deals with cruise line images and "View Cruise Details" links
            # Look for links that say "View Cruise Details"
            deal_links = soup.find_all('a', string=re.compile(r'View\s+Cruise\s+Details', re.I))
            
            if not deal_links:
                # Try alternative: look for divs containing cruise information
                logger.warning("No 'View Cruise Details' links found, trying alternative selectors")
                
                # Try to find parent containers of links
                all_links = soup.find_all('a', href=re.compile(r'cruise', re.I))
                deal_containers = []
                for link in all_links:
                    # Find parent container that likely holds the deal info
                    parent = link.find_parent(['div', 'article'])
                    if parent and parent not in deal_containers:
                        # Check if it has pricing or duration info
                        text = parent.get_text()
                        if ('From $' in text or 'pp' in text) and ('Night' in text or 'Days' in text):
                            deal_containers.append(parent)
                
                if not deal_containers:
                    logger.warning("No deal containers found - website structure may have changed")
                    return
                    
                logger.info(f"Found {len(deal_containers)} potential deals via alternative method")
                
                for container in deal_containers:
                    try:
                        deal = self._parse_deal(container)
                        if deal and not self._is_duplicate(deal):
                            self.deals.append(deal)
                    except Exception as e:
                        logger.warning(f"Error parsing deal: {e}")
                        continue
            else:
                # Each "View Cruise Details" link's parent container has the deal info
                # We need to go up the DOM tree to find the full deal card
                for idx, link in enumerate(deal_links):
                    try:
                        # Go up the DOM tree to find a container with substantial content
                        # The actual deal card is usually several levels up
                        container = link
                        best_container = None
                        
                        for level in range(15):  # Try going up 15 levels
                            container = container.find_parent()
                            if not container:
                                break
                            
                            # Count elements that suggest this is a deal container
                            text = container.get_text()
                            has_price = '$' in text and 'From' in text
                            has_duration = 'Night' in text
                            has_ship = any(ship_word in text for ship_word in ['Anthem', 'Voyager', 'Quantum', 'Carnival', 'Princess', 'Spirit', 'Edge', 'Encounter', 'Adventure', 'Splendor'])
                            has_departing = 'Departing' in text
                            has_destination = any(dest in text for dest in ['Eden', 'New Zealand', 'Pacific', 'Queensland', 'Vanuatu', 'Singapore', 'Alaska', 'Hawaii'])
                            
                            score = sum([has_price, has_duration, has_ship, has_departing])
                            
                            # We want a container with all key elements
                            if score >= 4:
                                best_container = container
                                break
                            elif score >= 3:
                                # Keep going to see if we can find a better one
                                if not best_container or score > sum([
                                    '$' in best_container.get_text() and 'From' in best_container.get_text(),
                                    'Night' in best_container.get_text(),
                                    any(ship_word in best_container.get_text() for ship_word in ['Anthem', 'Voyager', 'Quantum', 'Carnival', 'Princess', 'Spirit', 'Edge', 'Encounter', 'Adventure', 'Splendor']),
                                    'Departing' in best_container.get_text()
                                ]):
                                    best_container = container
                        
                        if best_container:
                            deal = self._parse_deal(best_container)
                            if deal and not self._is_duplicate(deal):
                                self.deals.append(deal)
                    except Exception as e:
                        logger.warning(f"Error parsing deal {idx}: {e}")
                        continue
        except Exception as e:
            logger.error(f"Error parsing page: {e}", exc_info=True)

    def _parse_deal(self, container) -> Optional[CruiseDeal]:
        """Parse individual deal from container"""
        try:
            # Get all text from container for easier searching
            full_text = container.get_text(separator=' ', strip=True)
            
            # Extract cruise line from image alt text or class names
            cruise_line = "Unknown"
            img = container.find('img')
            if img and img.get('alt'):
                cruise_line = img.get('alt', '')
            
            # Clean up cruise line name
            if 'carnival' in cruise_line.lower():
                cruise_line = 'Carnival'
            elif 'royal' in cruise_line.lower():
                cruise_line = 'Royal Caribbean'
            elif 'princess' in cruise_line.lower():
                cruise_line = 'Princess Cruises'
            elif 'celebrity' in cruise_line.lower():
                cruise_line = 'Celebrity Cruises'
            elif 'norwegian' in cruise_line.lower():
                cruise_line = 'Norwegian Cruise Line'
            elif 'cunard' in cruise_line.lower():
                cruise_line = 'Cunard'
            elif 'holland' in cruise_line.lower():
                cruise_line = 'Holland America'
            elif 'p&o' in cruise_line.lower():
                cruise_line = 'P&O Australia'
            elif 'azamara' in cruise_line.lower():
                cruise_line = 'Azamara'
            elif 'virgin' in cruise_line.lower():
                cruise_line = 'Virgin Voyages'
            
            # Extract ship name - look for text near fa-ship icon
            ship_name = "Unknown"
            # Find div with fa-ship class
            ship_icon = container.find(['i', 'span'], class_=re.compile(r'fa-ship'))
            if ship_icon:
                # Get the parent div's text
                ship_div = ship_icon.find_parent(['div', 'span'])
                if ship_div:
                    ship_text = ship_div.get_text(strip=True)
                    # Clean up the ship name
                    ship_name = ship_text.strip()
            
            # If not found, try regex patterns
            if ship_name == "Unknown":
                ship_patterns = [
                    r'(Anthem Of The Seas|Voyager Of The Seas|Quantum Of The Seas|Ovation Of The Seas)',
                    r'(Carnival \w+|Encounter|Adventure|Splendor|Luminosa)',
                    r'(Norwegian \w+|Spirit|Sun|Sky)',
                    r'(Celebrity \w+|Edge|Solstice)',
                    r'(Queen \w+|Anne|Elizabeth|Mary|Victoria)',
                    r'(Discovery Princess|Crown Princess|Diamond Princess|Grand Princess|Royal Princess|Coral Princess|Island Princess)',
                    r'(ms \w+)'
                ]
                for pattern in ship_patterns:
                    ship_match = re.search(pattern, full_text, re.IGNORECASE)
                    if ship_match:
                        ship_name = ship_match.group(1)
                        break
            
            # Extract destination - usually the title/heading
            destination = "Various"
            # Look for bold/heading text
            for tag in ['h1', 'h2', 'h3', 'h4', 'strong', 'b']:
                heading = container.find(tag)
                if heading:
                    dest_text = heading.get_text(strip=True)
                    if dest_text and len(dest_text) < 50:  # Reasonable destination length
                        destination = dest_text
                        break
            
            # Extract departure port - look for "Departing X" pattern
            departure_port = "Various Ports"
            port_match = re.search(r'Departing\s+([\w\s]+?)(?:\s+Cruise|\s+\d|\s+Twin|\s+Quad|$)', full_text, re.IGNORECASE)
            if port_match:
                departure_port = port_match.group(1).strip()
            
            # Extract cabin type - default to Interior, could be Twin/Quad
            cabin_type = "Interior"
            if 'Twin' in full_text:
                cabin_type = "Twin"
            elif 'Quad' in full_text:
                cabin_type = "Quad"
            
            # Extract price - look for "From $XXX pp" or "Twin From $XXX"
            total_price = 0.0
            price_patterns = [
                r'Twin From \$(\d{1,3}(?:,\d{3})*)',
                r'From \$(\d{1,3}(?:,\d{3})*)',
                r'\$(\d{1,3}(?:,\d{3})*)\s*pp'
            ]
            for pattern in price_patterns:
                price_match = re.search(pattern, full_text)
                if price_match:
                    total_price = float(price_match.group(1).replace(',', ''))
                    break
            
            # Extract duration - look for "X Nights" pattern
            duration = 0
            duration_match = re.search(r'(\d+)\s*Nights?', full_text, re.IGNORECASE)
            if duration_match:
                duration = int(duration_match.group(1))
            
            # Extract date - look for date patterns
            departure_date = datetime.now()
            date_patterns = [
                r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+(\d{1,2})(?:st|nd|rd|th)\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',
                r'(\d{1,2})/(\d{1,2})/(\d{4})',
            ]
            for pattern in date_patterns:
                date_match = re.search(pattern, full_text)
                if date_match:
                    try:
                        if len(date_match.groups()) == 4:
                            # Day name, day, month, year
                            day_name, day, month, year = date_match.groups()
                            date_str = f"{day} {month} {year}"
                            departure_date = datetime.strptime(date_str, '%d %B %Y')
                        elif len(date_match.groups()) == 3:
                            day, month, year = date_match.groups()
                            departure_date = datetime.strptime(f"{day}/{month}/{year}", '%d/%m/%Y')
                        break
                    except:
                        pass
            
            # Extract URL
            url = self._extract_url(container)
            
            # Extract special offers
            special_offers = ""
            if 'Bonus:' in full_text:
                bonus_match = re.search(r'Bonus:\s*([^\n]+)', full_text)
                if bonus_match:
                    special_offers = bonus_match.group(1).strip()
            elif 'Sale' in full_text:
                special_offers = "Sale Fares"
            
            # Skip if missing critical data
            if not total_price or not duration:
                return None
            
            price_per_day = total_price / duration if duration > 0 else float('inf')
            
            return CruiseDeal(
                cruise_line=cruise_line,
                ship_name=ship_name,
                destination=destination,
                departure_date=departure_date,
                duration_days=duration,
                total_price_aud=total_price,
                price_per_day=price_per_day,
                cabin_type=cabin_type,
                departure_port=departure_port,
                url=url,
                scraped_at=datetime.now(),
                special_offers=special_offers,
                image_url=None  # OzCruising scraper doesn't extract images (would require visiting each page)
            )
        except Exception as e:
            safe_print(f"⚠️  Error in _parse_deal: {e}")
            return None

    def _extract_text(self, container, class_patterns: List[str]) -> str:
        """Extract text from container using various class patterns"""
        for pattern in class_patterns:
            # Try exact class match
            elem = container.find(class_=re.compile(pattern, re.I))
            if elem:
                return elem.get_text(strip=True)
            
            # Try data attribute match
            elem = container.find(attrs={f'data-{pattern}': True})
            if elem:
                return elem.get(f'data-{pattern}', '') or elem.get_text(strip=True)
        
        return ""

    def _extract_price(self, text: str) -> float:
        """Extract price from text"""
        if not text:
            return 0.0
        # Remove currency symbols and extract number
        match = re.search(r'[\$]?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', text.replace(',', ''))
        if match:
            return float(match.group(1))
        return 0.0

    def _extract_duration(self, text: str) -> int:
        """Extract duration in days from text"""
        if not text:
            return 0
        # Look for patterns like "7 nights" or "7 days"
        match = re.search(r'(\d+)\s*(?:night|day)', text, re.I)
        if match:
            days = int(match.group(1))
            # Convert nights to days if needed
            if 'night' in text.lower():
                days += 1
            return days
        return 0

    def _extract_date(self, text: str) -> datetime:
        """Extract date from text"""
        if not text:
            return datetime.now()
        
        # Try various date formats
        patterns = [
            r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})',  # 15 January 2025
            r'(\d{1,2})/(\d{1,2})/(\d{4})',         # 15/01/2025
            r'(\d{4})-(\d{2})-(\d{2})',             # 2025-01-15
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    if len(match.groups()) == 3:
                        if '-' in text:
                            return datetime.strptime(match.group(0), '%Y-%m-%d')
                        elif '/' in text:
                            return datetime.strptime(match.group(0), '%d/%m/%Y')
                        else:
                            return datetime.strptime(match.group(0), '%d %B %Y')
                except:
                    pass
        
        return datetime.now()

    def _extract_url(self, container) -> str:
        """Extract URL from container"""
        # First priority: look for the actual cruise detail link
        detail_link = container.find('a', string=re.compile(r'View\s+Cruise\s+Details', re.I))
        if detail_link and detail_link.has_attr('href'):
            href = detail_link['href']
            if href.startswith('http'):
                return href
            else:
                return f"{self.BASE_URL}{href if href.startswith('/') else '/' + href}"
        
        # Second priority: find any link with cruise-related href
        cruise_links = container.find_all('a', href=re.compile(r'/(cruise|sailing|itinerary)', re.I))
        if cruise_links:
            for link in cruise_links:
                href = link['href']
                # Avoid generic pages like /cruise-specials
                if '/cruise-specials' not in href and '/cheap-cruises' not in href:
                    if href.startswith('http'):
                        return href
                    else:
                        return f"{self.BASE_URL}{href if href.startswith('/') else '/' + href}"
        
        # Fall back to any link
        link = container.find('a', href=True)
        if link:
            href = link['href']
            if href.startswith('http'):
                return href
            else:
                return f"{self.BASE_URL}{href if href.startswith('/') else '/' + href}"
        
        return self.BASE_URL
    
    def _is_duplicate(self, new_deal: CruiseDeal) -> bool:
        """Check if deal already exists in the list"""
        for deal in self.deals:
            if (deal.cruise_line == new_deal.cruise_line and
                deal.ship_name == new_deal.ship_name and
                deal.destination == new_deal.destination and
                deal.departure_date == new_deal.departure_date and
                deal.duration_days == new_deal.duration_days):
                return True
        return False
    
    def _enrich_deals_with_images(self):
        """Enrich deals by visiting detail pages to extract images and detailed info using Playwright"""
        import time
        import json
        import asyncio
        from playwright.sync_api import sync_playwright
        
        logger.info(f"Starting Playwright enrichment for {len(self.deals)} deals")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=self.session.headers.get('User-Agent', 'Mozilla/5.0'),
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()
            
            for i, deal in enumerate(self.deals):
                try:
                    logger.debug(f"Enriching deal {i+1}/{len(self.deals)}: {deal.url}")
                    
                    # Navigate to the detail page
                    page.goto(deal.url, wait_until='networkidle', timeout=30000)
                    
                    page.wait_for_timeout(2000)
                    
                    # Get the HTML after JavaScript has loaded
                    html_content = page.content()
                    soup = self._parse_html(html_content)
                    
                    if soup:
                        # Extract image if not present
                        if not deal.image_url:
                            image_url = self._extract_cruise_image(soup)
                            if image_url:
                                deal.image_url = image_url
                        
                        # Extract detailed information from tabs
                        itinerary = self._extract_itinerary_playwright(soup)
                        if itinerary:
                            deal.itinerary = json.dumps(itinerary)
                        
                        cabin_details = self._extract_cabin_details_playwright(soup)
                        if cabin_details:
                            deal.cabin_details = json.dumps(cabin_details)
                        
                        inclusions = self._extract_inclusions(soup)
                        if inclusions:
                            deal.inclusions = json.dumps(inclusions)
                        
                        logger.debug(f"Successfully enriched deal {i+1}/{len(self.deals)}")
                    
                    if (i + 1) % 50 == 0:
                        logger.info(f"Enriched {i+1}/{len(self.deals)} deals with details")
                        time.sleep(2)
                    elif (i + 1) % 10 == 0:
                        time.sleep(1)
                    else:
                        time.sleep(0.5)
                        
                except Exception as e:
                    logger.warning(f"Failed to enrich deal {i+1} ({deal.url}): {e}")
                    continue
            
            browser.close()
        
        logger.success(f"Completed enrichment of {len(self.deals)} deals")
    
    def _parse_html(self, html_content: str):
        """Parse HTML content with BeautifulSoup"""
        from bs4 import BeautifulSoup
        return BeautifulSoup(html_content, 'lxml')
    
    def _extract_cruise_image(self, soup) -> Optional[str]:
        """Extract the main cruise image from a detail page"""
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if 'cruise/large' in src or ('admin-ozcruising' in src and 'cruise' in src):
                if src.startswith('http'):
                    return src
                elif src.startswith('//'):
                    return f"https:{src}"
                else:
                    return f"{self.BASE_URL}{src if src.startswith('/') else '/' + src}"
        return None
    
    def _extract_itinerary_playwright(self, soup) -> Optional[List[dict]]:
        """Extract itinerary from JavaScript-rendered page"""
        try:
            itinerary = []
            
            # Find rows with port data attributes
            itinerary_rows = soup.find_all('tr', attrs={'data-cruiseline-portcode': True})
            
            if not itinerary_rows:
                logger.debug("No itinerary rows found with data-cruiseline-portcode")
                return None
            
            for idx, row in enumerate(itinerary_rows):
                try:
                    cells = row.find_all('td')
                    if len(cells) < 3:
                        continue
                    
                    port_info = {'day': idx + 1}
                    
                    date_text = cells[0].get_text(strip=True)
                    if date_text:
                        port_info['date'] = date_text
                    
                    arrival_text = cells[1].get_text(strip=True)
                    if arrival_text and arrival_text != '-':
                        port_info['arrival'] = arrival_text
                    
                    port_text = cells[2].get_text(strip=True)
                    if port_text:
                        port_info['port'] = port_text
                    
                    if len(cells) > 3:
                        departure_text = cells[3].get_text(strip=True)
                        if departure_text and departure_text != '-':
                            port_info['departure'] = departure_text
                    
                    if port_info.get('port'):
                        itinerary.append(port_info)
                        
                except Exception as e:
                    logger.debug(f"Error parsing itinerary row {idx}: {e}")
                    continue
            
            if itinerary:
                logger.info(f"Extracted itinerary with {len(itinerary)} ports")
                return itinerary
            else:
                logger.debug("No itinerary data extracted")
                return None
                
        except Exception as e:
            logger.warning(f"Error extracting itinerary: {e}")
            return None
    
    def _extract_cabin_details_playwright(self, soup) -> Optional[List[dict]]:
        """Extract cabin pricing from JavaScript-rendered page"""
        try:
            cabins = []
            
            # Look for all table rows - pricing is loaded via JavaScript
            all_rows = soup.find_all('tr')
            
            for row in all_rows:
                try:
                    cells = row.find_all('td')
                    if len(cells) < 4:
                        continue
                    
                    cell_texts = [c.get_text(strip=True) for c in cells]
                    
                    # Check if this looks like a cabin pricing row
                    if not any('$' in text or 'sold out' in text.lower() for text in cell_texts):
                        continue
                    
                    category = cells[0].get_text(strip=True)
                    if not category or len(category) > 3 or not category[0].isupper():
                        continue
                    
                    cabin_type = cells[1].get_text(strip=True)
                    if not cabin_type or len(cabin_type) < 5:
                        continue
                    
                    cabin_info = {
                        'category': category,
                        'type': cabin_type
                    }
                    
                    price_pp_text = cells[2].get_text(strip=True)
                    if 'sold out' not in price_pp_text.lower():
                        price_match = re.search(r'\$(\d{1,3}(?:,\d{3})*)', price_pp_text)
                        if price_match:
                            cabin_info['price_pp'] = float(price_match.group(1).replace(',', ''))
                    
                    if len(cells) > 3:
                        total_price_text = cells[3].get_text(strip=True)
                        if 'sold out' not in total_price_text.lower():
                            total_match = re.search(r'\$(\d{1,3}(?:,\d{3})*)', total_price_text)
                            if total_match:
                                cabin_info['total_price'] = float(total_match.group(1).replace(',', ''))
                    
                    if 'sold out' in price_pp_text.lower():
                        cabin_info['available'] = False
                    else:
                        disabled_button = row.find('button', disabled=True)
                        cabin_info['available'] = disabled_button is None
                    
                    cabins.append(cabin_info)
                    
                except Exception as e:
                    logger.debug(f"Error parsing cabin row: {e}")
                    continue
            
            if cabins:
                logger.info(f"Extracted {len(cabins)} cabin options")
                return cabins
            else:
                logger.debug("No cabin pricing extracted")
                return None
                
        except Exception as e:
            logger.warning(f"Error extracting cabin details: {e}")
            return None
    
    def _extract_itinerary(self, soup) -> Optional[List[dict]]:
        """Extract itinerary information from detail page
        
        Returns list of dicts with format:
        {
            'day': 1,
            'date': 'Thu 19 Feb 2026',
            'port': 'Brisbane',
            'arrival': '5:00 PM',
            'departure': '5:00 PM'
        }
        """
        try:
            itinerary = []
            
            # OzCruising has itinerary data in table rows with data-* attributes
            # Look for rows with data-cruiseline-portcode or similar attributes
            itinerary_rows = soup.find_all('tr', attrs={'data-cruiseline-portcode': True})
            
            if not itinerary_rows:
                itinerary_section = soup.find(['div', 'section'], id=re.compile(r'itinerary', re.I))
                if itinerary_section:
                    itinerary_rows = itinerary_section.find_all('tr')
            
            if itinerary_rows:
                day_counter = 1
                for row in itinerary_rows:
                    try:
                        cells = row.find_all('td')
                        if len(cells) < 1:
                            continue
                        
                        port_info = {'day': day_counter}
                        
                        # Extract port name from first cell
                        port_text = cells[0].get_text(strip=True)
                        if port_text and len(port_text) > 2:
                            # Clean up port name (remove country if present)
                            port_name = port_text.split('-')[0].strip() if '-' in port_text else port_text
                            port_info['port'] = port_name
                        
                        # Extract date if present (usually in second cell)
                        if len(cells) > 1:
                            date_text = cells[1].get_text(strip=True)
                            if date_text:
                                port_info['date'] = date_text
                        
                        # Extract arrival/departure times if present
                        if len(cells) > 2:
                            arrival_text = cells[2].get_text(strip=True)
                            if arrival_text and arrival_text != '-':
                                port_info['arrival'] = arrival_text
                        
                        if len(cells) > 3:
                            departure_text = cells[3].get_text(strip=True)
                            if departure_text and departure_text != '-':
                                port_info['departure'] = departure_text
                        
                        # Only add if we have a port name
                        if port_info.get('port'):
                            # Skip if it's just "Cruising" or "At Sea"
                            if 'cruising' not in port_info['port'].lower() or len(itinerary_rows) <= 3:
                                itinerary.append(port_info)
                                day_counter += 1
                            
                    except Exception as e:
                        logger.debug(f"Error parsing itinerary row: {e}")
                        continue
            
            return itinerary if itinerary else None
            
        except Exception as e:
            logger.warning(f"Error extracting itinerary: {e}")
            return None
    
    def _extract_cabin_details(self, soup) -> Optional[List[dict]]:
        """Extract cabin pricing and availability from detail page"""
        try:
            cabins = []
            
            # OzCruising loads pricing via JavaScript, look for table rows with pricing data
            all_rows = soup.find_all('tr')
            
            for row in all_rows:
                try:
                    cells = row.find_all('td')
                    if len(cells) < 4:
                        continue
                    
                    # Check if this looks like a pricing row (has $ or "Sold Out")
                    cell_texts = [c.get_text(strip=True) for c in cells]
                    if not any('$' in text or 'sold out' in text.lower() for text in cell_texts):
                        continue
                    
                    cabin_info = {}
                    
                    category = cells[0].get_text(strip=True)
                    if category and len(category) <= 3 and category.upper() == category:
                        cabin_info['category'] = category
                    else:
                        continue  # Not a valid category row
                    
                    cabin_type = cells[1].get_text(strip=True)
                    if cabin_type and len(cabin_type) > 3:
                        cabin_info['type'] = cabin_type
                    else:
                        continue
                    
                    price_pp_text = cells[2].get_text(strip=True)
                    if 'sold out' not in price_pp_text.lower():
                        price_match = re.search(r'\$(\d{1,3}(?:,\d{3})*)', price_pp_text)
                        if price_match:
                            cabin_info['price_pp'] = float(price_match.group(1).replace(',', ''))
                    
                    total_price_text = cells[3].get_text(strip=True)
                    if 'sold out' not in total_price_text.lower():
                        total_match = re.search(r'\$(\d{1,3}(?:,\d{3})*)', total_price_text)
                        if total_match:
                            cabin_info['total_price'] = float(total_match.group(1).replace(',', ''))
                    
                    if 'sold out' in price_pp_text.lower() or 'sold out' in total_price_text.lower():
                        cabin_info['available'] = False
                    else:
                        disabled_button = row.find('button', disabled=True)
                        cabin_info['available'] = disabled_button is None
                    
                    # Only add if we have essential fields
                    if cabin_info.get('category') and cabin_info.get('type'):
                        cabins.append(cabin_info)
                        
                except Exception as e:
                    logger.debug(f"Error parsing potential cabin row: {e}")
                    continue
            
            if cabins:
                logger.info(f"Extracted {len(cabins)} cabin options")
                return cabins
            else:
                logger.debug("No cabin pricing found")
                return None
            
        except Exception as e:
            logger.warning(f"Error extracting cabin details: {e}")
            return None
    
    def _extract_inclusions(self, soup) -> Optional[List[str]]:
        """Extract what's included in the cruise fare"""
        try:
            inclusions = []
            
            # Look for inclusions section
            inclusion_section = soup.find(['div', 'section', 'ul'], class_=re.compile(r'inclusion|include|whats.included', re.I))
            if not inclusion_section:
                for elem in soup.find_all(['h2', 'h3', 'h4']):
                    text = elem.get_text().lower()
                    if 'included' in text or 'inclusion' in text or "what's included" in text:
                        inclusion_section = elem.find_parent(['div', 'section'])
                        if not inclusion_section:
                            # Look for next sibling
                            inclusion_section = elem.find_next_sibling(['div', 'ul', 'section'])
                        break
            
            if inclusion_section:
                # Extract list items
                items = inclusion_section.find_all(['li', 'p'])
                for item in items:
                    text = item.get_text(strip=True)
                    if text and len(text) > 3 and len(text) < 200:
                        if not any(skip in text.lower() for skip in ['click here', 'read more', 'terms', 'conditions']):
                            inclusions.append(text)
            
            if not inclusions:
                inclusions = [
                    "Accommodation onboard",
                    "Meals in main dining rooms",
                    "Entertainment and activities",
                    "Port fees and taxes"
                ]
            
            return inclusions if inclusions else None
            
        except Exception as e:
            logger.warning(f"Error extracting inclusions: {e}")
            return None

