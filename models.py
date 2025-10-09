"""Data models for cruise deals"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class CruiseDeal:
    """Represents a cruise deal"""
    cruise_line: str
    ship_name: str
    destination: str
    departure_date: datetime
    duration_days: int
    total_price_aud: float
    price_per_day: float
    cabin_type: str
    departure_port: str
    url: str
    scraped_at: datetime
    special_offers: Optional[str] = None
    image_url: Optional[str] = None

    def __str__(self):
        return (
            f"\n{'='*80}\n"
            f"🚢 {self.cruise_line} - {self.ship_name}\n"
            f"{'='*80}\n"
            f"Destination:     {self.destination}\n"
            f"Departure Date:  {self.departure_date.strftime('%Y-%m-%d')}\n"
            f"Departure Port:  {self.departure_port}\n"
            f"Duration:        {self.duration_days} days\n"
            f"Cabin Type:      {self.cabin_type}\n"
            f"Total Price:     ${self.total_price_aud:.2f} AUD\n"
            f"Price Per Day:   ${self.price_per_day:.2f} AUD ⭐\n"
            f"Special Offers:  {self.special_offers or 'None'}\n"
            f"URL:             {self.url}\n"
            f"{'='*80}\n"
        )

    def is_good_deal(self, threshold: float = 100) -> bool:
        """Check if price per day is below threshold"""
        return self.price_per_day < threshold

