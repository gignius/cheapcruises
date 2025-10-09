"""Scraper for finding promo codes from various sources"""
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List
from promo_codes import PromoCode, PromoCodeStatus
import config


class PromoCodeScraper:
    """Scrapes promo codes from various sources"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        self.found_codes = []
    
    def scrape_royal_caribbean_official(self) -> List[PromoCode]:
        """Scrape official Royal Caribbean promotions page"""
        print("\n🔍 Scraping Royal Caribbean official promotions...")
        codes = []
        
        try:
            # Royal Caribbean promotions page
            url = "https://www.royalcaribbean.com/aus/en/cruise-deals"
            soup = self._get_page(url)
            
            if soup:
                # Look for promo code mentions in the page
                # This is a basic implementation - real scraping would need deeper analysis
                text = soup.get_text()
                
                # Look for patterns like "Code: XXXX" or "Promo Code: XXXX"
                code_patterns = [
                    r'[Cc]ode:\s*([A-Z0-9]{4,15})',
                    r'[Pp]romo\s+[Cc]ode:\s*([A-Z0-9]{4,15})',
                    r'[Uu]se\s+[Cc]ode\s+([A-Z0-9]{4,15})',
                ]
                
                found_codes_set = set()
                for pattern in code_patterns:
                    matches = re.finditer(pattern, text)
                    for match in matches:
                        found_codes_set.add(match.group(1))
                
                print(f"  └─ Found {len(found_codes_set)} potential codes on official site")
                
                for code_text in found_codes_set:
                    codes.append(PromoCode(
                        code=code_text,
                        cruise_line="Royal Caribbean",
                        description=f"Promotion code found on official website",
                        discount_type="unknown",
                        source_url=url,
                        status=PromoCodeStatus.UNKNOWN,
                        last_validated=datetime.now()
                    ))
        
        except Exception as e:
            print(f"❌ Error scraping Royal Caribbean official: {e}")
        
        return codes
    
    def scrape_partner_sites(self) -> List[PromoCode]:
        """Scrape known partner sites for promo codes"""
        print("\n🔍 Scraping partner sites...")
        codes = []
        
        # Note: Sydney Symphony and Village Roadshow codes are already in the database
        # This is where you'd add scrapers for other partner sites
        
        return codes
    
    def scrape_coupon_aggregators(self) -> List[PromoCode]:
        """Scrape coupon aggregator sites (with caution - many codes are invalid)"""
        print("\n🔍 Scraping coupon aggregator sites...")
        codes = []
        
        aggregator_sites = [
            {
                'name': 'BrokeScholar',
                'url': 'https://brokescholar.com/coupons/royal-caribbean',
                'selector_pattern': 'coupon'
            },
            # Add more aggregators as needed
        ]
        
        for site in aggregator_sites:
            try:
                print(f"  └─ Checking {site['name']}...")
                soup = self._get_page(site['url'])
                
                if soup:
                    # Look for promo codes in various formats
                    # This is a simplified version - real implementation would be site-specific
                    code_elements = soup.find_all(string=re.compile(r'\b[A-Z0-9]{4,15}\b'))
                    
                    found_count = 0
                    for element in code_elements:
                        # Extract potential codes
                        potential_codes = re.findall(r'\b([A-Z0-9]{4,15})\b', str(element))
                        
                        for code_text in potential_codes:
                            # Filter out common non-code words
                            if code_text in ['SALE', 'DISCOUNT', 'OFFER', 'PROMO', 'CODE']:
                                continue
                            
                            codes.append(PromoCode(
                                code=code_text,
                                cruise_line="Royal Caribbean",
                                description=f"Found on {site['name']} (unverified)",
                                discount_type="unknown",
                                source_url=site['url'],
                                status=PromoCodeStatus.UNKNOWN,
                                last_validated=datetime.now()
                            ))
                            found_count += 1
                    
                    print(f"     Found {found_count} potential codes")
            
            except Exception as e:
                print(f"  ❌ Error scraping {site['name']}: {e}")
        
        return codes
    
    def scrape_all(self) -> List[PromoCode]:
        """Scrape all sources"""
        all_codes = []
        
        # Scrape official sources first (most reliable)
        all_codes.extend(self.scrape_royal_caribbean_official())
        
        # Partner sites
        all_codes.extend(self.scrape_partner_sites())
        
        # Coupon aggregators (least reliable)
        all_codes.extend(self.scrape_coupon_aggregators())
        
        # Remove duplicates
        unique_codes = {}
        for code in all_codes:
            key = f"{code.code}_{code.cruise_line}"
            if key not in unique_codes:
                unique_codes[key] = code
        
        self.found_codes = list(unique_codes.values())
        
        print(f"\n✅ Total unique codes found: {len(self.found_codes)}")
        
        return self.found_codes
    
    def _get_page(self, url: str) -> BeautifulSoup:
        """Fetch and parse a page"""
        try:
            response = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'lxml')
        except Exception as e:
            print(f"  ❌ Error fetching {url}: {e}")
            return None


class PromoCodeValidator:
    """Validates promo codes by attempting to apply them"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.USER_AGENT,
        })
    
    def validate_code(self, promo_code: PromoCode) -> bool:
        """
        Attempt to validate a promo code
        
        Note: Full validation requires automated checkout testing,
        which is complex and may violate Terms of Service.
        This is a placeholder for basic validation logic.
        """
        print(f"  └─ Validating code: {promo_code.code}")
        
        # For now, we'll rely on the known valid/invalid status
        # Real implementation would:
        # 1. Navigate to booking page
        # 2. Select a test cruise
        # 3. Attempt to apply the promo code
        # 4. Check if it's accepted or rejected
        # 5. Capture any error messages
        
        # This requires Selenium or Playwright for full automation
        # and must be done carefully to not abuse the booking system
        
        if promo_code.status == PromoCodeStatus.VALID:
            return True
        elif promo_code.status == PromoCodeStatus.INVALID or promo_code.status == PromoCodeStatus.EXPIRED:
            return False
        
        # For unknown codes, we can't validate without real checkout testing
        print(f"     Cannot validate without checkout testing")
        return False
    
    def validate_codes_batch(self, promo_codes: List[PromoCode]) -> List[PromoCode]:
        """Validate multiple promo codes"""
        validated = []
        
        print(f"\n🔍 Validating {len(promo_codes)} promo codes...")
        print("⚠️  Note: Full validation requires automated checkout testing")
        
        for code in promo_codes:
            is_valid = self.validate_code(code)
            if is_valid:
                code.status = PromoCodeStatus.VALID
            code.last_validated = datetime.now()
            validated.append(code)
        
        return validated

