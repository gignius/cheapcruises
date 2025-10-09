"""Solr API scraper for Holland America Line"""
import requests
from datetime import datetime
from typing import List
from models import CruiseDeal
from base_scraper import safe_print


class HollandAmericaAPIScraper:
    """Direct Solr API scraper for Holland America"""
    
    BASE_URL = "https://www.hollandamerica.com"
    API_URL = f"{BASE_URL}/search/halcruisesearch"
    
    @property
    def name(self) -> str:
        return "Holland America (API)"

    def scrape(self) -> List[CruiseDeal]:
        """Scrape cruise deals from Holland America's Solr API"""
        safe_print(f"\n🔍 Scraping {self.name} via Solr API...")
        deals = []
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': f'{self.BASE_URL}/en_US/cruise-search.html'
        }
        
        # Pagination
        page_size = 50
        max_results = 500
        
        for start in range(0, max_results, page_size):
            params = {
                'start': start,
                'rows': page_size,
                'country': 'au',
                'language': 'en',
                'fq': 'departDate:[NOW/DAY+1DAY TO *]',  # Future cruises only
                'fq': '{!tag=collapse}{!collapse field=itineraryId}',  # Collapse duplicates
                'expand': 'true',
                'expand.rows': page_size
            }
            
            try:
                safe_print(f"  Fetching cruises {start}-{start+page_size}...")
                response = requests.get(self.API_URL, params=params, headers=headers, timeout=15)
                
                if response.status_code != 200:
                    safe_print(f"  ⚠️  API returned status {response.status_code}")
                    break
                
                data = response.json()
                docs = data.get('response', {}).get('docs', [])
                
                if not docs:
                    break
                
                safe_print(f"  Found {len(docs)} cruises")
                
                # Parse each cruise
                for doc in docs:
                    deal = self._parse_cruise(doc)
                    if deal and not self._is_duplicate(deals, deal):
                        deals.append(deal)
                
                # If fewer than page size, we're done
                if len(docs) < page_size:
                    break
                    
            except Exception as e:
                safe_print(f"  ⚠️  Error: {e}")
                break
        
        safe_print(f"✅ Successfully scraped {len(deals)} deals from {self.name}")
        return deals
    
    def _parse_cruise(self, doc: dict) -> CruiseDeal:
        """Parse a Holland America cruise document"""
        try:
            # Extract ship name (format: "Noordam#@#NO")
            ship_full = doc.get('shipName', 'Unknown#@#XX')
            ship_name = ship_full.split('#@#')[0] if '#@#' in ship_full else ship_full
            
            # Add "ms " prefix if not present
            if not ship_name.lower().startswith('ms '):
                ship_name = f"ms {ship_name}"
            
            # Extract destination
            destinations = doc.get('en_au_destinationNames_ss', [])
            destination = destinations[0].split('#@#')[0] if destinations else 'Various'
            
            # Extract duration (in days)
            duration = doc.get('duration', 0)
            
            # Extract departure port
            embark_ports = doc.get('embarkPortNames', [])
            departure_port = embark_ports[0].split('#@#')[0] if embark_ports else 'Various'
            
            # Extract price (use AUD if available, otherwise USD)
            price = doc.get('price_AUD_RESTRICTED', doc.get('sortPrice_AUD', doc.get('sortPrice_USD', 0)))
            
            # Extract departure date
            depart_date_str = doc.get('departDate', '')
            try:
                # Format: "2025-10-18T00:00:00Z"
                departure_date = datetime.fromisoformat(depart_date_str.replace('Z', '+00:00'))
            except:
                departure_date = datetime.now()
            
            # Build URL from contentPath
            content_path = doc.get('contentPath', '')
            if content_path:
                # contentPath format: "/find-a-cruise/p6h35a/n674"
                url = f"{self.BASE_URL}{content_path}.html"
            else:
                itinerary_id = doc.get('itineraryId', '')
                url = f"{self.BASE_URL}/en_US/find-a-cruise/{itinerary_id.lower()}.html" if itinerary_id else self.BASE_URL
            
            # Extract image
            cruise_image = doc.get('cruiseOverviewImage', '')
            image_url = f"{self.BASE_URL}{cruise_image}" if cruise_image and not cruise_image.startswith('http') else cruise_image
            
            # Calculate price per day
            price_per_day = price / duration if duration > 0 else float('inf')
            
            if price <= 0 or duration <= 0:
                return None
            
            return CruiseDeal(
                cruise_line="Holland America",
                ship_name=ship_name,
                destination=destination,
                departure_date=departure_date,
                duration_days=duration,
                total_price_aud=price,
                price_per_day=price_per_day,
                cabin_type="Interior",
                departure_port=departure_port,
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

