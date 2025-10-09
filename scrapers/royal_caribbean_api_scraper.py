"""GraphQL API scraper for Royal Caribbean Australia"""
import requests
from datetime import datetime
from typing import List
from models import CruiseDeal
from base_scraper import safe_print


class RoyalCaribbeanAPIScraper:
    """Direct GraphQL API scraper for Royal Caribbean (no browser needed!)"""
    
    BASE_URL = "https://www.royalcaribbean.com"
    GRAPH_URL = f"{BASE_URL}/graph"
    
    @property
    def name(self) -> str:
        return "Royal Caribbean Australia (GraphQL API)"

    def scrape(self) -> List[CruiseDeal]:
        """Scrape cruise deals from Royal Caribbean's GraphQL API"""
        safe_print(f"\n🔍 Scraping {self.name} via GraphQL...")
        deals = []
        
        # Search multiple destination combinations
        destination_filters = [
            "destination:AUSTL",  # Australia
            "destination:SOPAC",  # South Pacific
            "destination:FAR.E",  # Far East / Asia
            "destination:TPACI",  # Transpacific
            "destination:CARIB",  # Caribbean
            "destination:ALCAN",  # Alaska & Canada
            "destination:EUROP",  # Europe
            "",  # All destinations
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': 'https://www.royalcaribbean.com.au/aus/en/cruise-search',
            'Origin': 'https://www.royalcaribbean.com.au'
        }
        
        for filter_str in destination_filters:
            try:
                # Build minimal GraphQL query
                query = f"""
{{
  cruiseSearch(filters: "{filter_str}") {{
    results {{
      cruises {{
        id
        productViewLink
        lowestPriceSailing {{
          lowestStateroomClassPrice {{
            price {{
              value
            }}
          }}
        }}
        masterSailing {{
          itinerary {{
            name
            ship {{
              name
            }}
            departurePort {{
              name
              region
            }}
            totalNights
          }}
        }}
        sailings {{
          id
        }}
      }}
    }}
  }}
}}
"""
                
                safe_print(f"  Fetching cruises for: {filter_str or 'All destinations'}...")
                
                params = {'query': query}
                response = requests.get(self.GRAPH_URL, params=params, headers=headers, timeout=15)
                
                if response.status_code != 200:
                    safe_print(f"  ⚠️  API returned status {response.status_code}")
                    continue
                
                data = response.json()
                
                # Extract cruises
                cruises = (data.get('data', {})
                          .get('cruiseSearch', {})
                          .get('results', {})
                          .get('cruises', []))
                
                if not cruises:
                    continue
                
                safe_print(f"  Found {len(cruises)} cruises")
                
                # Parse each cruise
                for cruise in cruises:
                    deal = self._parse_cruise(cruise)
                    if deal and not self._is_duplicate(deals, deal):
                        deals.append(deal)
                
            except Exception as e:
                safe_print(f"  ⚠️  Error fetching {filter_str}: {e}")
                continue
        
        safe_print(f"✅ Successfully scraped {len(deals)} deals from {self.name}")
        return deals
    
    def _parse_cruise(self, cruise: dict) -> CruiseDeal:
        """Parse a Royal Caribbean cruise into a CruiseDeal"""
        try:
            # Extract master sailing info
            master = cruise.get('masterSailing', {})
            itinerary = master.get('itinerary', {})
            ship = itinerary.get('ship', {})
            port = itinerary.get('departurePort', {})
            
            # Extract lowest price sailing
            lowest = cruise.get('lowestPriceSailing', {})
            price_info = lowest.get('lowestStateroomClassPrice', {})
            price_obj = price_info.get('price', {})
            price = price_obj.get('value', 0)
            
            # Extract details
            ship_name = ship.get('name', 'Unknown')
            destination_name = itinerary.get('name', 'Various')
            duration_nights = itinerary.get('totalNights', 0)
            duration_days = duration_nights + 1
            departure_port_name = f"{port.get('name', 'Unknown')}, {port.get('region', '')}"
            
            # Extract sailing date from the first sailing ID
            sailings = cruise.get('sailings', [])
            departure_date = datetime.now()
            if sailings:
                # Sailing ID format: "QN03K088_2027-02-05"
                sailing_id = sailings[0].get('id', '')
                if '_' in sailing_id:
                    date_str = sailing_id.split('_')[1]
                    try:
                        departure_date = datetime.strptime(date_str, '%Y-%m-%d')
                    except:
                        pass
            
            # Build URL - Fix currency and country parameters for Australia
            product_link = cruise.get('productViewLink', '')
            # productViewLink format: "cruises/itinerary/3-night-brisbane-getaway-from-brisbane-on-quantum/QN03BNE-1451917990?sail-date=2027-02-05&currency=AUD&country=AUS"
            if product_link:
                # Remove any existing currency/country params and add correct ones for Australia
                base_link = product_link.split('?')[0]
                # Extract sail date if present
                sail_date = ''
                if '?sail-date=' in product_link or '&sail-date=' in product_link:
                    import re
                    match = re.search(r'sail-date=([^&]+)', product_link)
                    if match:
                        sail_date = match.group(1)
                
                # Rebuild URL with Australian parameters
                url = f"https://www.royalcaribbean.com.au/aus/en/{base_link}"
                if sail_date:
                    url += f"?sail-date={sail_date}&currency=AUD&country=AUS"
                else:
                    url += "?currency=AUD&country=AUS"
            else:
                url = self.BASE_URL
            
            # Calculate price per day
            price_per_day = price / duration_days if duration_days > 0 else float('inf')
            
            if price <= 0 or duration_days <= 0:
                return None
            
            # Extract image (Royal Caribbean provides images in itinerary media)
            image_url = None
            media = itinerary.get('media', {})
            images = media.get('images', [])
            if images and len(images) > 0:
                image_path = images[0].get('path', '')
                if image_path:
                    # Convert to full URL
                    if image_path.startswith('http'):
                        image_url = image_path
                    else:
                        image_url = f"https://www.royalcaribbean.com{image_path}"
            
            return CruiseDeal(
                cruise_line="Royal Caribbean",
                ship_name=ship_name,
                destination=destination_name,
                departure_date=departure_date,
                duration_days=duration_days,
                total_price_aud=price,
                price_per_day=price_per_day,
                cabin_type="Interior",
                departure_port=departure_port_name,
                url=url,
                scraped_at=datetime.now(),
                special_offers=None,
                image_url=image_url
            )
            
        except Exception as e:
            safe_print(f"  ⚠️  Error parsing cruise: {e}")
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

