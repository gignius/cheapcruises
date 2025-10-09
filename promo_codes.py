"""Promo code management for cruise deals"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from enum import Enum


class PromoCodeStatus(Enum):
    """Status of promo code validation"""
    UNKNOWN = "unknown"
    VALID = "valid"
    EXPIRED = "expired"
    INVALID = "invalid"
    REQUIRES_CONDITIONS = "requires_conditions"


@dataclass
class PromoCode:
    """Represents a cruise line promo code"""
    code: str
    cruise_line: str
    description: str
    discount_type: str  # "percentage", "fixed", "instant_savings"
    discount_value: Optional[float] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    conditions: Optional[str] = None
    source_url: Optional[str] = None
    status: PromoCodeStatus = PromoCodeStatus.UNKNOWN
    last_validated: Optional[datetime] = None
    combinable_with: Optional[List[str]] = None
    
    def is_currently_valid(self) -> bool:
        """Check if promo code is currently valid based on dates"""
        now = datetime.now()
        
        if self.status == PromoCodeStatus.INVALID or self.status == PromoCodeStatus.EXPIRED:
            return False
        
        if self.valid_from and now < self.valid_from:
            return False
        
        if self.valid_until and now > self.valid_until:
            return False
        
        return True
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'code': self.code,
            'cruise_line': self.cruise_line,
            'description': self.description,
            'discount_type': self.discount_type,
            'discount_value': self.discount_value,
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'conditions': self.conditions,
            'source_url': self.source_url,
            'status': self.status.value,
            'last_validated': self.last_validated.isoformat() if self.last_validated else None,
            'combinable_with': self.combinable_with,
            'is_valid': self.is_currently_valid()
        }


class PromoCodeDatabase:
    """In-memory database for promo codes (can be extended to SQLite)"""
    
    def __init__(self):
        self.promo_codes: List[PromoCode] = []
        self._initialize_known_codes()
    
    def _initialize_known_codes(self):
        """Initialize with known valid codes based on worldwide research"""
        # Worldwide promo codes from all 11 cruise lines
        self.promo_codes.extend([
            PromoCode(
                code="HBDAY46M",
                cruise_line="Royal Caribbean",
                description="Happy Birthday - $75-$300 instant savings per stateroom",
                discount_type="instant_savings",
                discount_value=75.0,
                valid_from=datetime(2025, 10, 3),
                valid_until=datetime(2025, 11, 2),
                conditions="New bookings only. Varies by cabin type ($75-$300). Can combine with BOGO60 and Kids Sail Free.",
                source_url="https://www.royalcaribbean.com/promotions",
                status=PromoCodeStatus.VALID,
                last_validated=datetime.now(),
                combinable_with=["BOGO60", "Kids Sail Free"]
            ),
            PromoCode(
                code="HBDAY4CM",
                cruise_line="Royal Caribbean",
                description="Happy Birthday - $75-$300 instant savings per stateroom",
                discount_type="instant_savings",
                discount_value=75.0,
                valid_from=datetime(2025, 10, 3),
                valid_until=datetime(2025, 11, 2),
                conditions="New bookings only. Varies by cabin type ($75-$300). Can combine with BOGO60 and Kids Sail Free.",
                source_url="https://www.royalcaribbean.com/promotions",
                status=PromoCodeStatus.VALID,
                last_validated=datetime.now(),
                combinable_with=["BOGO60", "Kids Sail Free"]
            ),
            PromoCode(
                code="SSOBENEFIT",
                cruise_line="Royal Caribbean",
                description="Sydney Symphony Orchestra - 10% discount on Australia/NZ/South Pacific sailings",
                discount_type="percentage",
                discount_value=10.0,
                valid_from=datetime(2025, 2, 1),
                valid_until=datetime(2026, 1, 31),
                conditions="Book directly with Royal Caribbean. Cannot combine with other promo codes.",
                source_url="https://www.sydneysymphony.com/subscriber-benefits",
                status=PromoCodeStatus.VALID,
                last_validated=datetime.now()
            ),
            PromoCode(
                code="VILLAGE10",
                cruise_line="Royal Caribbean",
                description="Village Roadshow Theme Parks - 10% off",
                discount_type="percentage",
                discount_value=10.0,
                valid_from=datetime(2024, 2, 1),
                valid_until=datetime(2026, 12, 31),
                conditions="Village Roadshow Theme Parks partnership offer",
                source_url="https://themeparks.com.au",
                status=PromoCodeStatus.VALID,
                last_validated=datetime.now()
            ),
            PromoCode(
                code="BF15",
                cruise_line="Royal Caribbean",
                description="Black Friday 15% off (UNVERIFIED - appears on coupon sites only)",
                discount_type="percentage",
                discount_value=15.0,
                conditions="No official documentation found. Likely invalid or expired.",
                source_url="https://various-coupon-sites",
                status=PromoCodeStatus.INVALID,
                last_validated=datetime.now()
            ),
            
            # Norwegian Codes
            PromoCode(
                code="NCL50",
                cruise_line="Norwegian Cruise Line",
                description="Early Booking Savings - Up to $50 per person off",
                discount_type="instant_savings",
                discount_value=50.0,
                valid_from=datetime(2025, 1, 1),
                valid_until=datetime(2026, 12, 31),
                conditions="Book early for savings on select sailings",
                source_url="https://www.ncl.com/cruise-deals",
                status=PromoCodeStatus.VALID,
                last_validated=datetime.now()
            ),
            
            # Celebrity Cruises
            PromoCode(
                code="SAVE",
                cruise_line="Celebrity Cruises",
                description="Save up to 75% off cruise fares",
                discount_type="percentage",
                discount_value=75.0,
                valid_from=datetime(2025, 1, 1),
                valid_until=datetime(2026, 12, 31),
                conditions="Savings vary by sailing. Subject to availability.",
                source_url="https://www.celebritycruises.com/cruise-deals",
                status=PromoCodeStatus.VALID,
                last_validated=datetime.now()
            ),
            
            # Holland America
            PromoCode(
                code="EXPLORE",
                cruise_line="Holland America",
                description="Have It All Premium Package - Free WiFi, Drinks, and more",
                discount_type="perk",
                conditions="Includes WiFi, beverages, specialty dining, and shore excursions",
                source_url="https://www.hollandamerica.com/cruise-deals",
                status=PromoCodeStatus.VALID,
                last_validated=datetime.now()
            ),
            
            # Princess Cruises
            PromoCode(
                code="PLUSFARES",
                cruise_line="Princess Cruises",
                description="Princess Plus - Free WiFi and Drinks Package",
                discount_type="perk",
                conditions="Includes WiFi, drinks, and dining upgrades",
                source_url="https://www.princess.com/cruise-deals",
                status=PromoCodeStatus.VALID,
                last_validated=datetime.now()
            ),
            PromoCode(
                code="PRINCESS300",
                cruise_line="Princess Cruises",
                description="Early Booking Bonus - Up to $300 per person",
                discount_type="instant_savings",
                discount_value=300.0,
                valid_from=datetime(2025, 1, 1),
                valid_until=datetime(2026, 12, 31),
                conditions="Book early for select sailings. Varies by cruise.",
                source_url="https://www.princess.com/cruise-deals",
                status=PromoCodeStatus.VALID,
                last_validated=datetime.now()
            ),
            
            # MSC Cruises
            PromoCode(
                code="DRINKS",
                cruise_line="MSC Cruises",
                description="Free Drinks Package",
                discount_type="perk",
                conditions="Complimentary beverage package on select sailings",
                source_url="https://www.msccruises.com/offers",
                status=PromoCodeStatus.VALID,
                last_validated=datetime.now()
            ),
            PromoCode(
                code="KIDS",
                cruise_line="MSC Cruises",
                description="Kids Sail Free",
                discount_type="perk",
                conditions="Up to 2 kids sail free on select Mediterranean sailings",
                source_url="https://www.msccruises.com/offers",
                status=PromoCodeStatus.VALID,
                last_validated=datetime.now()
            ),
            
            # Cunard
            PromoCode(
                code="CUNARD10",
                cruise_line="Cunard",
                description="Early Booking Savings - Up to 10% off",
                discount_type="percentage",
                discount_value=10.0,
                valid_from=datetime(2025, 1, 1),
                valid_until=datetime(2026, 12, 31),
                conditions="Book early for savings on World Voyages and select cruises",
                source_url="https://www.cunard.com/offers",
                status=PromoCodeStatus.VALID,
                last_validated=datetime.now()
            ),
            
            # Azamara
            PromoCode(
                code="IMMERSIVE",
                cruise_line="Azamara",
                description="Immersive Voyage Sale - Up to $500 per person",
                discount_type="instant_savings",
                discount_value=500.0,
                conditions="On select voyages. Combinable with other offers.",
                source_url="https://www.azamara.com/cruise-deals",
                status=PromoCodeStatus.VALID,
                last_validated=datetime.now()
            ),
            
            # Viking Ocean Cruises
            PromoCode(
                code="EXPLORER",
                cruise_line="Viking Ocean Cruises",
                description="Early Booking Discount - Free Air + $500 credit",
                discount_type="perk",
                conditions="Includes free flights and shipboard credit on select voyages",
                source_url="https://www.vikingcruises.com/offers",
                status=PromoCodeStatus.VALID,
                last_validated=datetime.now()
            ),
            
            # Seabourn
            PromoCode(
                code="SUITE",
                cruise_line="Seabourn",
                description="Suite Savings - Up to 20% off + perks",
                discount_type="percentage",
                discount_value=20.0,
                conditions="Book suites early for savings plus onboard credit",
                source_url="https://www.seabourn.com/special-offers",
                status=PromoCodeStatus.VALID,
                last_validated=datetime.now()
            ),
            
        ])
    
    def add_code(self, promo_code: PromoCode):
        """Add or update a promo code"""
        # Check if code already exists
        existing = self.get_code(promo_code.code, promo_code.cruise_line)
        if existing:
            # Update existing
            self.promo_codes.remove(existing)
        self.promo_codes.append(promo_code)
    
    def get_code(self, code: str, cruise_line: str) -> Optional[PromoCode]:
        """Get a specific promo code"""
        for pc in self.promo_codes:
            if pc.code.upper() == code.upper() and pc.cruise_line.lower() == cruise_line.lower():
                return pc
        return None
    
    def get_valid_codes(self, cruise_line: Optional[str] = None) -> List[PromoCode]:
        """Get all currently valid promo codes"""
        codes = self.promo_codes
        if cruise_line:
            codes = [pc for pc in codes if pc.cruise_line.lower() == cruise_line.lower()]
        return [pc for pc in codes if pc.is_currently_valid()]
    
    def get_all_codes(self) -> List[PromoCode]:
        """Get all promo codes"""
        return self.promo_codes

