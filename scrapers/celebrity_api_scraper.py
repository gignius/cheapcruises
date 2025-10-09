"""GraphQL API scraper for Celebrity Cruises (uses Royal Caribbean's GraphQL)"""
import requests
from datetime import datetime
from typing import List
from models import CruiseDeal
from base_scraper import safe_print


class CelebrityAPIScraper:
    """Direct GraphQL API scraper for Celebrity Cruises"""
    
    BASE_URL = "https://www.celebritycruises.com"
    GRAPH_URL = f"{BASE_URL}/graph"
    
    @property
    def name(self) -> str:
        return "Celebrity Cruises (GraphQL API)"

    def scrape(self) -> List[CruiseDeal]:
        """Scrape cruise deals from Celebrity's GraphQL API"""
        safe_print(f"\n🔍 Scraping {self.name} via GraphQL...")
        deals = []
        
        # Search multiple destinations
        destination_filters = [
            "destination:CARIB",  # Caribbean
            "destination:ALCAN",  # Alaska & Canada
            "destination:EUROP",  # Europe
            "destination:AUSTL",  # Australia
            "destination:SOPAC",  # South Pacific
            "destination:FAR.E",  # Asia
            "",  # All destinations
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': f'{self.BASE_URL}/cruise-search',
            'Origin': self.BASE_URL
        }
        
        for filter_str in destination_filters:
            try:
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
                cruises = (data.get('data', {})
                          .get('cruiseSearch', {})
                          .get('results', {})
                          .get('cruises', []))
                
                if not cruises:
                    continue
                
                safe_print(f"  Found {len(cruises)} cruises")
                
                for cruise in cruises:
                    deal = self._parse_cruise(cruise)
                    if deal and not self._is_duplicate(deals, deal):
                        deals.append(deal)
                
            except Exception as e:
                safe_print(f"  ⚠️  Error: {e}")
                continue
        
        safe_print(f"✅ Successfully scraped {len(deals)} deals from {self.name}")
        return deals
    
    def _parse_cruise(self, cruise: dict) -> CruiseDeal:
        """Parse a Celebrity cruise"""
        try:
            master = cruise.get('masterSailing', {})
            itinerary = master.get('itinerary', {})
            ship = itinerary.get('ship', {})
            port = itinerary.get('departurePort', {})
            
            lowest = cruise.get('lowestPriceSailing', {})
            price = lowest.get('lowestStateroomClassPrice', {}).get('price', {}).get('value', 0)
            
            ship_name = ship.get('name', 'Unknown')
            destination_name = itinerary.get('name', 'Various')
            duration_nights = itinerary.get('totalNights', 0)
            duration_days = duration_nights + 1
            departure_port_name = f"{port.get('name', 'Unknown')}, {port.get('region', '')}"
            
            # Extract sailing date
            sailings = cruise.get('sailings', [])
            departure_date = datetime.now()
            if sailings:
                sailing_id = sailings[0].get('id', '')
                if '_' in sailing_id:
                    date_str = sailing_id.split('_')[1]
                    try:
                        departure_date = datetime.strptime(date_str, '%Y-%m-%d')
                    except:
                        pass
            
            # Build URL - Fix to use Australian currency
            product_link = cruise.get('productViewLink', '')
            if product_link:
                # Replace country/currency in URL
                import re
                url = f"{self.BASE_URL}/{product_link}"
                # Replace country=USA with country=AUS and currency if present
                url = re.sub(r'country=USA', 'country=AUS', url)
                url = re.sub(r'&cCD=CO', '&cCD=AU', url)
                # Note: Celebrity may not have AUD pricing available, prices might still be in USD on their site
            else:
                url = self.BASE_URL
            
            price_per_day = price / duration_days if duration_days > 0 else float('inf')
            
            if price <= 0 or duration_days <= 0:
                return None
            
            # Extract image
            image_url = None
            media = itinerary.get('media', {})
            images = media.get('images', [])
            if images and len(images) > 0:
                image_path = images[0].get('path', '')
                if image_path:
                    image_url = f"https://www.celebritycruises.com{image_path}" if not image_path.startswith('http') else image_path
            
            return CruiseDeal(
                cruise_line="Celebrity Cruises",
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
        for deal in deals:
            if (deal.cruise_line == new_deal.cruise_line and
                deal.ship_name == new_deal.ship_name and
                deal.destination == new_deal.destination and
                deal.departure_date == new_deal.departure_date and
                deal.duration_days == new_deal.duration_days):
                return True
        return False

