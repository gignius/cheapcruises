"""Filtered OzCruising scraper - ONLY for lines we can't scrape directly"""
from typing import List
from models import CruiseDeal
from .ozcruising_scraper import OzCruisingScraper


class FilteredOzCruisingScraper(OzCruisingScraper):
    """OzCruising scraper filtered to only return specific cruise lines we can't scrape directly"""
    
    # Only these cruise lines (the ones we can't scrape via their own APIs)
    ALLOWED_LINES = {
        'Princess Cruises',
        'Cunard',
        'P&O Australia',
        'MSC',
        'MSC Cruises',
        '[ Msc ]',
        'Seabourn',
        '[ Seabourn ]',
        'Viking Ocean Cruises',
        '[ VikingOceanCruises ]',
        'Azamara',
    }
    
    @property
    def name(self) -> str:
        return "OzCruising (Filtered: Princess, Cunard, P&O, MSC, Seabourn, Viking, Azamara)"
    
    def scrape(self) -> List[CruiseDeal]:
        """Scrape but filter to only allowed cruise lines"""
        all_deals = super().scrape()
        
        # Filter to only the cruise lines we can't scrape directly
        filtered_deals = [
            deal for deal in all_deals
            if deal.cruise_line in self.ALLOWED_LINES
        ]
        
        from base_scraper import safe_print
        safe_print(f"  Filtered {len(all_deals)} deals down to {len(filtered_deals)} (only Princess/Cunard/P&O/MSC/Seabourn/Viking/Azamara)")
        
        return filtered_deals

