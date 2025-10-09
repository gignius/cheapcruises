"""API scraper for Norwegian Cruise Line"""
import requests
from datetime import datetime
from typing import List
from models import CruiseDeal
from base_scraper import safe_print


class NorwegianAPIScraper:
    """Direct API scraper for Norwegian Cruise Line"""
    
    BASE_URL = "https://www.ncl.com"
    API_URL = f"{BASE_URL}/au/en/api/vacations/v2/itineraries"
    
    # Ship code to name mapping
    SHIP_NAMES = {
        'LUNA': 'Norwegian Luna',
        'SPIRIT': 'Norwegian Spirit',
        'SUN': 'Norwegian Sun',
        'JADE': 'Norwegian Jade',
        'JEWEL': 'Norwegian Jewel',
        'PEARL': 'Norwegian Pearl',
        'GEM': 'Norwegian Gem',
        'SKY': 'Norwegian Sky',
        'BREAKAWAY': 'Norwegian Breakaway',
        'GETAWAY': 'Norwegian Getaway',
        'ESCAPE': 'Norwegian Escape',
        'JOY': 'Norwegian Joy',
        'BLISS': 'Norwegian Bliss',
        'ENCORE': 'Norwegian Encore',
        'PRIMA': 'Norwegian Prima',
        'VIVA': 'Norwegian Viva',
        'AQUA': 'Norwegian Aqua',
        'PRIDE_AMER': 'Pride of America',
    }
    
    # Destination code mapping
    DESTINATIONS = {
        'CARIBBEAN': 'Caribbean',
        'BAHAMAS': 'Bahamas',
        'ALASKA': 'Alaska',
        'EUROPE': 'Europe',
        'BERMUDA': 'Bermuda',
        'MEXICO': 'Mexico',
        'HAWAII': 'Hawaii',
        'CANADA': 'Canada & New England',
        'TRANSATLANTIC': 'Transatlantic',
        'TRANSPACIFIC': 'Transpacific',
        'PANAMA': 'Panama Canal',
        'SOUTHAMERICA': 'South America',
        'AFRICA': 'Africa',
        'ASIA': 'Asia',
        'AUSTRALIA': 'Australia & New Zealand',
    }
    
    @property
    def name(self) -> str:
        return "Norwegian Cruise Line (API)"

    def scrape(self) -> List[CruiseDeal]:
        """Scrape cruise deals from Norwegian's API"""
        safe_print(f"\n🔍 Scraping {self.name} via REST API...")
        deals = []
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': f'{self.BASE_URL}/cruises/search'
        }
        
        params = {
            'guests': 2,
        }
        
        try:
            safe_print(f"  Fetching Norwegian itineraries...")
            response = requests.get(self.API_URL, params=params, headers=headers, timeout=20)
            
            if response.status_code != 200:
                safe_print(f"  ⚠️  API returned status {response.status_code}")
                return deals
            
            data = response.json()
            
            if not isinstance(data, list):
                safe_print(f"  ⚠️  Unexpected data format")
                return deals
            
            safe_print(f"  Found {len(data)} itineraries")
            
            # Parse each itinerary
            for itinerary in data:
                # Each itinerary has multiple sailings with different dates
                sailings = itinerary.get('sailings', [])
                
                for sailing in sailings:
                    deal = self._parse_sailing(itinerary, sailing)
                    if deal and not self._is_duplicate(deals, deal):
                        deals.append(deal)
            
            safe_print(f"✅ Successfully scraped {len(deals)} deals from {self.name}")
            
        except Exception as e:
            safe_print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        return deals
    
    def _parse_sailing(self, itinerary: dict, sailing: dict) -> CruiseDeal:
        """Parse a Norwegian sailing into a CruiseDeal"""
        try:
            # Extract ship info
            ship_code = itinerary.get('shipCode', 'UNKNOWN')
            ship_name = self.SHIP_NAMES.get(ship_code, f'Norwegian {ship_code}')
            
            # Extract destination
            dest_codes = itinerary.get('destinationCodes', [])
            destination = self.DESTINATIONS.get(dest_codes[0], dest_codes[0]) if dest_codes else 'Various'
            
            # Extract duration
            duration = itinerary.get('duration', 0)
            
            # Extract port
            embark_port = itinerary.get('embarkationPort', {})
            port_code = embark_port.get('code', 'Unknown')
            departure_port = port_code  # Could map this to full names
            
            # Extract pricing - use INSIDE cabin price
            pricing = sailing.get('pricing', [])
            price = 0
            cabin_type = "Interior"
            
            for price_option in pricing:
                if price_option.get('status') == 'AVAILABLE':
                    if price_option.get('code') == 'INSIDE':
                        price = price_option.get('combinedPrice', 0)
                        cabin_type = "Interior"
                        break
                    elif not price and price_option.get('combinedPrice', 0) > 0:
                        # Use first available price
                        price = price_option.get('combinedPrice', 0)
                        cabin_type = price_option.get('code', 'Interior')
            
            # Extract departure date (Unix timestamp in milliseconds)
            depart_timestamp = sailing.get('departureDate', 0)
            if depart_timestamp:
                departure_date = datetime.fromtimestamp(depart_timestamp / 1000)
            else:
                departure_date = datetime.now()
            
            # Build URL
            itinerary_code = itinerary.get('code', '')
            sail_id = sailing.get('sailId', '')
            package_id = sailing.get('packageId', '')
            
            # NCL URL format
            url = f"{self.BASE_URL}/au/en/cruises/{itinerary_code.lower()}?sailingId={sail_id}" if itinerary_code and sail_id else self.BASE_URL
            
            # Calculate price per day
            price_per_day = price / duration if duration > 0 else float('inf')
            
            if price <= 0 or duration <= 0:
                return None
            
            # Norwegian doesn't provide images in their itinerary API, use a default ship image
            # We could fetch individual cruise pages for images, but that would be too slow
            image_url = f"https://www.ncl.com/sites/default/files/ships/{itinerary.get('shipCode', 'default').lower()}_hero.jpg"
            
            return CruiseDeal(
                cruise_line="Norwegian Cruise Line",
                ship_name=ship_name,
                destination=destination,
                departure_date=departure_date,
                duration_days=duration,
                total_price_aud=price,
                price_per_day=price_per_day,
                cabin_type=cabin_type,
                departure_port=departure_port,
                url=url,
                scraped_at=datetime.now(),
                special_offers=None,
                image_url=image_url
            )
            
        except Exception as e:
            safe_print(f"  ⚠️  Error parsing sailing: {e}")
            return None
    
    def _is_duplicate(self, deals: List[CruiseDeal], new_deal: CruiseDeal) -> bool:
        for deal in deals:
            if (deal.cruise_line == new_deal.cruise_line and
                deal.ship_name == new_deal.ship_name and
                deal.destination == new_deal.destination and
                deal.departure_date == new_deal.departure_date and
                deal.duration_days == new_deal.duration_days):
                return True
        return False

