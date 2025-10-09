"""Scraper for Carnival Cruise Line"""
import re
import json
from datetime import datetime
from typing import List
from base_scraper import BaseScraper, safe_print
from models import CruiseDeal


class CarnivalScraper(BaseScraper):
    """Scraper for Carnival Cruise Line website"""
    
    BASE_URL = "https://www.carnival.com"
    AU_BASE_URL = "https://www.carnival.com.au"
    SEARCH_URL = f"{AU_BASE_URL}/cruise-deals"
    
    @property
    def name(self) -> str:
        return "Carnival Cruise Line"

    def scrape(self) -> List[CruiseDeal]:
        """Scrape cruise deals from Carnival"""
        safe_print(f"\n🔍 Scraping {self.name}...")
        self.deals = []
        
        try:
            soup = self.get_page(self.SEARCH_URL)
            if not soup:
                safe_print(f"❌ Failed to fetch {self.SEARCH_URL}")
                return self.deals
            
            # Try to find JSON data
            json_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get('@type') in ['Product', 'Offer']:
                        deal = self._parse_json_deal(data)
                        if deal:
                            self.deals.append(deal)
                    elif isinstance(data, list):
                        for item in data:
                            if item.get('@type') in ['Product', 'Offer']:
                                deal = self._parse_json_deal(item)
                                if deal:
                                    self.deals.append(deal)
                except:
                    pass
            
            # Parse HTML structure
            deal_containers = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'(cruise|deal|offer|card|sailing|package)', re.I))
            
            if not deal_containers:
                # Alternative selectors
                deal_containers = soup.find_all(attrs={'data-cruise': True})
                if not deal_containers:
                    deal_containers = soup.find_all(attrs={'data-sailing-id': True})
            
            if deal_containers:
                safe_print(f"📦 Found {len(deal_containers)} potential deals in HTML")
                
                for container in deal_containers:
                    try:
                        deal = self._parse_html_deal(container)
                        if deal and deal not in self.deals:
                            self.deals.append(deal)
                    except Exception as e:
                        safe_print(f"⚠️  Error parsing deal: {e}")
                        continue
            
            safe_print(f"✅ Successfully scraped {len(self.deals)} deals from {self.name}")
            
        except Exception as e:
            safe_print(f"❌ Error scraping {self.name}: {e}")
        
        return self.deals

    def _parse_json_deal(self, data: dict) -> CruiseDeal:
        """Parse deal from JSON-LD data"""
        try:
            offers = data.get('offers', {})
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            
            price = float(offers.get('price', 0))
            
            name = data.get('name', '')
            description = data.get('description', '')
            
            # Extract duration
            duration_match = re.search(r'(\d+)\s*(?:Night|Day)', name + ' ' + description, re.I)
            duration = int(duration_match.group(1)) if duration_match else 7
            
            if 'night' in (name + description).lower() and duration_match:
                duration += 1
            
            price_per_day = price / duration if duration > 0 else float('inf')
            
            return CruiseDeal(
                cruise_line="Carnival",
                ship_name=self._extract_ship_name(name, description),
                destination=self._extract_destination(name, description),
                departure_date=datetime.now(),
                duration_days=duration,
                total_price_aud=price,
                price_per_day=price_per_day,
                cabin_type="Interior",
                departure_port="Various Ports",
                url=data.get('url', self.SEARCH_URL),
                scraped_at=datetime.now(),
                special_offers=offers.get('description', '')
            )
        except:
            return None

    def _parse_html_deal(self, container) -> CruiseDeal:
        """Parse deal from HTML container"""
        # Ship name
        ship_elem = container.find(['h2', 'h3', 'h4', 'div', 'span'], class_=re.compile(r'ship|vessel', re.I))
        if not ship_elem:
            ship_elem = container.find(attrs={'data-ship-name': True})
        ship_name = ship_elem.get_text(strip=True) if ship_elem else "Unknown"
        if ship_elem and ship_elem.has_attr('data-ship-name'):
            ship_name = ship_elem['data-ship-name']
        
        # Destination
        dest_elem = container.find(['div', 'span', 'p'], class_=re.compile(r'destination|itinerary|region', re.I))
        if not dest_elem:
            dest_elem = container.find(attrs={'data-destination': True})
        destination = dest_elem.get_text(strip=True) if dest_elem else "Various"
        if dest_elem and dest_elem.has_attr('data-destination'):
            destination = dest_elem['data-destination']
        
        # Price
        price_elem = container.find(['span', 'div'], class_=re.compile(r'price|cost|from|rate', re.I))
        if not price_elem:
            price_elem = container.find(attrs={'data-price': True})
        price_text = price_elem.get_text(strip=True) if price_elem else "0"
        if price_elem and price_elem.has_attr('data-price'):
            price_text = price_elem['data-price']
        total_price = self._extract_price(price_text)
        
        # Duration
        duration_elem = container.find(['span', 'div'], class_=re.compile(r'duration|night|day|length', re.I))
        if not duration_elem:
            duration_elem = container.find(attrs={'data-duration': True})
        duration_text = duration_elem.get_text(strip=True) if duration_elem else "7 nights"
        if duration_elem and duration_elem.has_attr('data-duration'):
            duration_text = duration_elem['data-duration']
        duration = self._extract_duration(duration_text)
        
        # Date
        date_elem = container.find(['span', 'div', 'time'], class_=re.compile(r'date|departure|sailing', re.I))
        if not date_elem:
            date_elem = container.find(attrs={'data-date': True})
        date_text = date_elem.get_text(strip=True) if date_elem else ""
        if date_elem and date_elem.has_attr('data-date'):
            date_text = date_elem['data-date']
        departure_date = self._extract_date(date_text)
        
        # Port
        port_elem = container.find(['span', 'div'], class_=re.compile(r'port|depart|embark', re.I))
        if not port_elem:
            port_elem = container.find(attrs={'data-port': True})
        departure_port = port_elem.get_text(strip=True) if port_elem else "Various Ports"
        if port_elem and port_elem.has_attr('data-port'):
            departure_port = port_elem['data-port']
        
        # Cabin type
        cabin_elem = container.find(['span', 'div'], class_=re.compile(r'cabin|room|stateroom|category', re.I))
        cabin_type = cabin_elem.get_text(strip=True) if cabin_elem else "Interior"
        
        # URL
        url = self._extract_url(container)
        
        # Special offers
        offer_elem = container.find(['span', 'div', 'p'], class_=re.compile(r'offer|promo|special|bonus', re.I))
        special_offers = offer_elem.get_text(strip=True) if offer_elem else None
        
        if not total_price or not duration:
            return None
        
        price_per_day = total_price / duration if duration > 0 else float('inf')
        
        return CruiseDeal(
            cruise_line="Carnival",
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
            special_offers=special_offers
        )

    def _extract_ship_name(self, name: str, description: str) -> str:
        """Extract ship name from text"""
        text = name + ' ' + description
        # Carnival ship names
        ships = ['Celebration', 'Mardi Gras', 'Venezia', 'Jubilee', 'Vista', 'Horizon',
                 'Panorama', 'Dream', 'Magic', 'Breeze', 'Conquest', 'Glory', 'Liberty',
                 'Valor', 'Freedom', 'Triumph', 'Victory', 'Legend', 'Miracle', 'Pride',
                 'Spirit', 'Splendor', 'Sunshine', 'Luminosa', 'Encounter', 'Radiance']
        
        for ship in ships:
            if ship.lower() in text.lower():
                return f"Carnival {ship}"
        
        return "Unknown"

    def _extract_destination(self, name: str, description: str) -> str:
        """Extract destination from text"""
        text = name + ' ' + description
        destinations = ['Caribbean', 'Mediterranean', 'Alaska', 'Europe', 'Bahamas',
                       'Mexico', 'Hawaii', 'Bermuda', 'Canada', 'New England',
                       'Pacific', 'Australia', 'New Zealand', 'Asia']
        
        for dest in destinations:
            if dest.lower() in text.lower():
                return dest
        
        return "Various"

    def _extract_price(self, text: str) -> float:
        """Extract price from text"""
        if not text:
            return 0.0
        text = text.replace(',', '').replace('$', '').replace('AUD', '').replace('USD', '')
        match = re.search(r'(\d+(?:\.\d{2})?)', text)
        if match:
            return float(match.group(1))
        return 0.0

    def _extract_duration(self, text: str) -> int:
        """Extract duration in days from text"""
        if not text:
            return 7
        match = re.search(r'(\d+)\s*(?:night|day)', text, re.I)
        if match:
            days = int(match.group(1))
            if 'night' in text.lower():
                days += 1
            return days
        return 7

    def _extract_date(self, text: str) -> datetime:
        """Extract date from text"""
        if not text:
            return datetime.now()
        
        patterns = [
            r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})',
            r'(\d{1,2})/(\d{1,2})/(\d{4})',
            r'(\d{4})-(\d{2})-(\d{2})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
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
        link = container.find('a', href=True)
        if link:
            href = link['href']
            if href.startswith('http'):
                return href
            else:
                base = self.AU_BASE_URL
                return f"{base}{href if href.startswith('/') else '/' + href}"
        return self.SEARCH_URL

