"""Selenium-based scraper to fetch 2-person and 4-person interior pricing from OzCruising"""
import time
from typing import Optional, Tuple
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from loguru import logger
import re


class PricingScraper:
    """Scrape 2-person and 4-person interior pricing from OzCruising using Selenium"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        
    def _setup_driver(self):
        """Setup headless Chrome driver"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
    def _close_driver(self):
        """Close the driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def get_pricing(self, cruise_url: str) -> Tuple[Optional[float], Optional[float]]:
        """
        Get both 2-person and 4-person interior pricing for a cruise
        
        Returns:
            Tuple of (price_2p, price_4p) or (None, None) if not found
        """
        if not cruise_url:
            return None, None
            
        try:
            if not self.driver:
                self._setup_driver()
            
            logger.debug(f"Fetching pricing from: {cruise_url}")
            self.driver.get(cruise_url)
            
            # Wait for page to load
            time.sleep(2)
            
            # Click on "Pricing" tab if it exists
            try:
                pricing_tab = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Pricing')]"))
                )
                pricing_tab.click()
                time.sleep(1)
            except TimeoutException:
                logger.debug("No Pricing tab found, assuming pricing is already visible")
            
            price_2p = None
            price_4p = None
            
            # Try to find the cabin size selector
            try:
                # Look for the 2-person selector/button and click it
                selector_2p = self.driver.find_element(By.XPATH, "//select[@name='cabin_size']//option[@value='2'] | //button[contains(text(), '2')]")
                selector_2p.click()
                time.sleep(1.5)
                
                # Extract cheapest interior cabin price for 2 people
                price_2p = self._extract_cheapest_interior_price()
                logger.debug(f"2-person interior price: ${price_2p}")
                
            except NoSuchElementException:
                logger.debug("Could not find 2-person cabin selector, trying table parsing")
                # Fallback: parse pricing table directly
                price_2p = self._parse_pricing_table(cabin_size=2)
            
            try:
                # Look for the 4-person selector/button and click it
                selector_4p = self.driver.find_element(By.XPATH, "//select[@name='cabin_size']//option[@value='4'] | //button[contains(text(), '4')]")
                selector_4p.click()
                time.sleep(1.5)
                
                # Extract cheapest interior cabin price for 4 people
                price_4p = self._extract_cheapest_interior_price()
                logger.debug(f"4-person interior price: ${price_4p}")
                
            except NoSuchElementException:
                logger.debug("Could not find 4-person cabin selector, trying table parsing")
                # Fallback: parse pricing table directly
                price_4p = self._parse_pricing_table(cabin_size=4)
            
            return price_2p, price_4p
            
        except Exception as e:
            logger.error(f"Error fetching pricing from {cruise_url}: {e}")
            return None, None
    
    def _extract_cheapest_interior_price(self) -> Optional[float]:
        """Extract the cheapest interior cabin total price from the current page"""
        try:
            # Find all table rows
            rows = self.driver.find_elements(By.TAG_NAME, "tr")
            
            interior_prices = []
            
            for row in rows:
                try:
                    text = row.text.lower()
                    
                    # Check if this row is for an interior cabin
                    if 'interior' not in text:
                        continue
                    
                    # Check if it's sold out
                    if 'sold out' in text:
                        continue
                    
                    # Extract total cabin price (4th column typically)
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 4:
                        total_price_text = cells[3].text
                        price_match = re.search(r'\$(\d{1,3}(?:,\d{3})*)', total_price_text)
                        if price_match:
                            price = float(price_match.group(1).replace(',', ''))
                            interior_prices.append(price)
                    
                except Exception as e:
                    logger.debug(f"Error parsing row: {e}")
                    continue
            
            # Return the cheapest price
            if interior_prices:
                return min(interior_prices)
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting interior price: {e}")
            return None
    
    def _parse_pricing_table(self, cabin_size: int = 2) -> Optional[float]:
        """
        Parse the pricing table directly when cabin size selector is not available
        
        Args:
            cabin_size: 2 or 4 for number of passengers
        """
        try:
            page_source = self.driver.page_source
            
            # Look for pricing table in the page source
            # This is a fallback method when JavaScript selectors don't work
            if cabin_size == 2:
                # Look for patterns like "Interior $XXX $YYY" where second number is total for 2p
                pattern = r'Interior.*?\$(\d{1,3}(?:,\d{3})*)\s+\$(\d{1,3}(?:,\d{3})*)'
            else:
                # For 4-person, we need to look for quad pricing
                pattern = r'quad.*?\$(\d{1,3}(?:,\d{3})*)'
            
            matches = re.finditer(pattern, page_source, re.IGNORECASE)
            prices = []
            
            for match in matches:
                if cabin_size == 2:
                    # Use the total price (second group)
                    price_str = match.group(2)
                else:
                    price_str = match.group(1)
                    
                price = float(price_str.replace(',', ''))
                prices.append(price)
            
            if prices:
                return min(prices)
            
            return None
            
        except Exception as e:
            logger.warning(f"Error parsing pricing table: {e}")
            return None
    
    def close(self):
        """Close the scraper and cleanup"""
        self._close_driver()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


if __name__ == "__main__":
    # Test the scraper
    scraper = PricingScraper(headless=True)
    
    test_url = "https://www.ozcruising.com.au/cruise/cl25-fn15dec25"
    price_2p, price_4p = scraper.get_pricing(test_url)
    
    print(f"2-person interior price: ${price_2p}")
    print(f"4-person interior price: ${price_4p}")
    
    scraper.close()
