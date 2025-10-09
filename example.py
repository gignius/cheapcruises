"""
Example script showing how to use the cruise scrapers programmatically
"""
from scrapers import OzCruisingScraper, RoyalCaribbeanScraper, CarnivalScraper
from alerts import AlertSystem
import config


def example_basic_usage():
    """Basic example: scrape one website"""
    print("Example 1: Basic Usage - Scraping OzCruising")
    print("-" * 50)
    
    scraper = OzCruisingScraper()
    deals = scraper.scrape()
    
    print(f"Found {len(deals)} total deals")
    
    # Filter for good deals
    good_deals = scraper.get_good_deals(threshold=100)
    print(f"Found {len(good_deals)} deals under $100/day")
    
    if good_deals:
        print("\nBest deal:")
        best_deal = min(good_deals, key=lambda x: x.price_per_day)
        print(best_deal)


def example_multiple_scrapers():
    """Example: scrape multiple websites"""
    print("\n\nExample 2: Multiple Scrapers")
    print("-" * 50)
    
    scrapers = [
        OzCruisingScraper(),
        RoyalCaribbeanScraper(),
        CarnivalScraper()
    ]
    
    all_good_deals = []
    
    for scraper in scrapers:
        deals = scraper.scrape()
        good_deals = scraper.get_good_deals(threshold=100)
        all_good_deals.extend(good_deals)
        print(f"{scraper.name}: {len(good_deals)} deals under $100/day")
    
    print(f"\nTotal good deals: {len(all_good_deals)}")


def example_custom_threshold():
    """Example: use custom threshold"""
    print("\n\nExample 3: Custom Threshold")
    print("-" * 50)
    
    scraper = RoyalCaribbeanScraper()
    deals = scraper.scrape()
    
    # Try different thresholds
    for threshold in [80, 100, 120, 150]:
        good_deals = [d for d in deals if d.price_per_day < threshold]
        print(f"Deals under ${threshold}/day: {len(good_deals)}")


def example_filtering():
    """Example: custom filtering"""
    print("\n\nExample 4: Custom Filtering")
    print("-" * 50)
    
    scraper = CarnivalScraper()
    deals = scraper.scrape()
    
    # Filter by destination
    caribbean_deals = [d for d in deals if 'caribbean' in d.destination.lower()]
    print(f"Caribbean deals: {len(caribbean_deals)}")
    
    # Filter by duration
    week_long = [d for d in deals if 6 <= d.duration_days <= 8]
    print(f"Week-long cruises: {len(week_long)}")
    
    # Filter by price and duration
    affordable_week = [
        d for d in deals 
        if d.price_per_day < 100 and 6 <= d.duration_days <= 8
    ]
    print(f"Affordable week-long cruises: {len(affordable_week)}")


def example_alerts():
    """Example: using alerts"""
    print("\n\nExample 5: Alerts")
    print("-" * 50)
    
    scraper = OzCruisingScraper()
    deals = scraper.scrape()
    good_deals = scraper.get_good_deals(threshold=100)
    
    if good_deals:
        # Console alert (always works)
        AlertSystem.send_console_alert(good_deals)
        
        # Save to file
        AlertSystem.save_to_file(good_deals, "my_deals.txt")
        
        # Email alert (requires configuration)
        if config.EMAIL_ENABLED:
            AlertSystem.send_email_alert(good_deals)


def example_accessing_deal_data():
    """Example: accessing deal properties"""
    print("\n\nExample 6: Accessing Deal Data")
    print("-" * 50)
    
    scraper = RoyalCaribbeanScraper()
    deals = scraper.scrape()
    
    if deals:
        deal = deals[0]
        print(f"Cruise Line: {deal.cruise_line}")
        print(f"Ship: {deal.ship_name}")
        print(f"Destination: {deal.destination}")
        print(f"Date: {deal.departure_date.strftime('%Y-%m-%d')}")
        print(f"Duration: {deal.duration_days} days")
        print(f"Total Price: ${deal.total_price_aud:.2f}")
        print(f"Price/Day: ${deal.price_per_day:.2f}")
        print(f"Cabin: {deal.cabin_type}")
        print(f"Port: {deal.departure_port}")
        print(f"URL: {deal.url}")
        print(f"Good deal? {deal.is_good_deal(100)}")


if __name__ == "__main__":
    print("="*50)
    print("CRUISE SCRAPER EXAMPLES")
    print("="*50)
    
    # Uncomment the examples you want to run:
    
    # example_basic_usage()
    # example_multiple_scrapers()
    # example_custom_threshold()
    # example_filtering()
    # example_alerts()
    # example_accessing_deal_data()
    
    print("\n\nℹ️  Uncomment the examples in example.py to run them")
    print("   Or run the main scraper: python main.py")

