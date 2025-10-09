"""API-based scraper for Carnival Cruise Line Australia"""
import requests
from datetime import datetime
from typing import List
from models import CruiseDeal
from base_scraper import safe_print


class CarnivalAPIScraper:
    """Direct API scraper for Carnival Australia (no browser needed!)"""
    
    BASE_URL = "https://www.carnival.com.au"
    API_URL = f"{BASE_URL}/cruisesearch/api/search"
    
    @property
    def name(self) -> str:
        return "Carnival Australia (API)"

    def scrape(self) -> List[CruiseDeal]:
        """Scrape cruise deals from Carnival's search API"""
        safe_print(f"\n🔍 Scraping {self.name} via direct API...")
        deals = []
        
        # Destinations to search
        destinations = [
            "TP,NZ,O,U,X",  # Transpacific, NZ, South Pacific, Australia, Asia
            "A,BH,BM,NN,C,E,H,M,P",  # Alaska, Bahamas, Bermuda, Canada, Caribbean, Europe, Hawaii, Mexico, Panama
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': f'{self.BASE_URL}/cruise-search'
        }
        
        for dest_codes in destinations:
            # Search with pagination
            page_num = 1
            max_pages = 20  # Limit to prevent infinite loops
            
            while page_num <= max_pages:
                params = {
                    'pageNumber': page_num,
                    'numadults': 2,
                    'dest': dest_codes,
                    'pagesize': 30,  # Get more per page
                    'sort': 'FromPrice',
                    'locality': '7',  # Australia
                    'currency': 'AUD',
                }
                
                try:
                    safe_print(f"  Fetching page {page_num} for destinations: {dest_codes[:30]}...")
                    response = requests.get(self.API_URL, params=params, headers=headers, timeout=15)
                    
                    if response.status_code != 200:
                        safe_print(f"  ⚠️  API returned status {response.status_code}")
                        break
                    
                    data = response.json()
                    
                    if 'results' not in data or 'itineraries' not in data['results']:
                        safe_print(f"  ⚠️  No itineraries in response")
                        break
                    
                    itineraries = data['results']['itineraries']
                    
                    if not itineraries:
                        # No more results
                        break
                    
                    safe_print(f"  Found {len(itineraries)} cruises on page {page_num}")
                    
                    # Parse each itinerary
                    for itin in itineraries:
                        deal = self._parse_itinerary(itin)
                        if deal and not self._is_duplicate(deals, deal):
                            deals.append(deal)
                    
                    # Check if there are more pages
                    if len(itineraries) < params['pagesize']:
                        # Last page
                        break
                    
                    page_num += 1
                    
                except Exception as e:
                    safe_print(f"  ⚠️  Error fetching page {page_num}: {e}")
                    break
        
        safe_print(f"✅ Successfully scraped {len(deals)} deals from {self.name}")
        return deals
    
    def _parse_itinerary(self, itin: dict) -> CruiseDeal:
        """Parse a Carnival itinerary into a CruiseDeal"""
        try:
            lead = itin.get('leadSailing', {})
            
            # Extract basic info
            ship_name = itin.get('shipName', 'Unknown')
            duration = itin.get('dur', 0)
            departure_port = itin.get('departurePortName', 'Unknown')
            destination = itin.get('regionName', 'Various')
            
            # Extract image
            image = itin.get('image', '')
            image_url = f"{self.BASE_URL}{image}" if image and not image.startswith('http') else image
            
            # Extract pricing
            from_price = lead.get('fromPrice', 0)
            
            # Extract date
            departure_date_str = lead.get('departureDate', '')
            try:
                departure_date = datetime.fromisoformat(departure_date_str.replace('Z', '+00:00'))
            except:
                departure_date = datetime.now()
            
            # Build URL - create proper booking link with sail date and details
            cruise_code = itin.get('code', '')
            ship_code = itin.get('shipCode', '').lower()
            port_code = itin.get('departurePortCode', '').lower()
            
            # Get the sailing date for the URL
            departure_date_iso = lead.get('departureDate', '')
            sail_date = departure_date_iso[:10] if departure_date_iso else ''  # Get YYYY-MM-DD
            
            # Carnival URL format: /itinerary/{cruise-code}/{ship}-{port}-{duration}day?date={sail-date}
            # Or simpler: /cruises/{cruise-code}?saildate={date}
            if sail_date and cruise_code:
                url = f"{self.BASE_URL}/cruises/{cruise_code.lower()}?saildate={sail_date}"
            else:
                url = f"{self.BASE_URL}/cruises/{cruise_code.lower()}" if cruise_code else self.BASE_URL
            
            # Calculate duration in days (Carnival uses nights)
            duration_days = duration + 1 if duration > 0 else 1
            
            # Calculate price per day
            price_per_day = from_price / duration_days if duration_days > 0 else float('inf')
            
            # Cabin type from meta code
            meta_code = lead.get('leadMetaCode', 'IS')
            cabin_map = {
                'IS': 'Interior',
                'OS': 'Oceanview',
                'BS': 'Balcony',
                'SU': 'Suite'
            }
            cabin_type = cabin_map.get(meta_code, 'Interior')
            
            if from_price <= 0 or duration_days <= 0:
                return None
            
            return CruiseDeal(
                cruise_line="Carnival",
                ship_name=ship_name,
                destination=destination,
                departure_date=departure_date,
                duration_days=duration_days,
                total_price_aud=from_price,
                price_per_day=price_per_day,
                cabin_type=cabin_type,
                departure_port=departure_port,
                url=url,
                scraped_at=datetime.now(),
                special_offers=None,
                image_url=image_url
            )
            
        except Exception as e:
            safe_print(f"  ⚠️  Error parsing itinerary: {e}")
            return None
    
    def _is_duplicate(self, deals: List[CruiseDeal], new_deal: CruiseDeal) -> bool:
        """Check if deal already exists"""
        for deal in deals:
            if (deal.cruise_line == new_deal.cruise_line and
                deal.ship_name == new_deal.ship_name and
                deal.destination == new_deal.destination and
                deal.departure_date == new_deal.departure_date and
                deal.duration_days == new_deal.duration_days):
                return True
        return False

