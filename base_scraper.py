"""Base scraper class"""
import requests
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod
from typing import List
from datetime import datetime
import time
import config
from models import CruiseDeal


def safe_print(text):
    """Print with Unicode error handling"""
    try:
        print(text)
    except UnicodeEncodeError:
        ascii_text = text.encode('ascii', 'ignore').decode('ascii')
        print(ascii_text if ascii_text else "[Output contains unsupported characters]")


class BaseScraper(ABC):
    """Base class for all cruise scrapers"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.deals = []

    def get_page(self, url: str, retry: int = 3) -> BeautifulSoup:
        """Fetch and parse a page with retry logic"""
        for attempt in range(retry):
            try:
                response = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
                response.raise_for_status()
                return BeautifulSoup(response.content, 'lxml')
            except requests.RequestException as e:
                safe_print(f"❌ Error fetching {url} (attempt {attempt + 1}/{retry}): {e}")
                if attempt < retry - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise
        return None

    @abstractmethod
    def scrape(self) -> List[CruiseDeal]:
        """Scrape cruise deals - must be implemented by subclasses"""
        pass

    def get_good_deals(self, threshold: float = None) -> List[CruiseDeal]:
        """Filter deals below the price threshold"""
        if threshold is None:
            threshold = config.PRICE_THRESHOLD
        return [deal for deal in self.deals if deal.is_good_deal(threshold)]

    @property
    @abstractmethod
    def name(self) -> str:
        """Scraper name"""
        pass

