"""Main script to run cruise deal scrapers"""
import sys
import argparse
from typing import List
from datetime import datetime
import config
from models import CruiseDeal
from scrapers import OzCruisingScraper, RoyalCaribbeanScraper, CarnivalScraper
from alerts import AlertSystem


def main():
    """Main function to run all scrapers"""
    parser = argparse.ArgumentParser(
        description='Scrape cruise deals and find bargains under $100/day AUD'
    )
    parser.add_argument(
        '--scrapers',
        nargs='+',
        choices=['ozcruising', 'royal', 'carnival', 'all'],
        default=['all'],
        help='Which scrapers to run (default: all)'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=config.PRICE_THRESHOLD,
        help=f'Price threshold per day in AUD (default: {config.PRICE_THRESHOLD})'
    )
    parser.add_argument(
        '--email',
        action='store_true',
        help='Send email alerts (requires email configuration)'
    )
    parser.add_argument(
        '--save',
        action='store_true',
        help='Save results to file'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output filename for saved results'
    )
    
    args = parser.parse_args()
    
    print("="*80)
    print("🚢 CRUISE DEAL SCRAPER 🚢")
    print("="*80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Price threshold: ${args.threshold}/day AUD")
    print("="*80)
    
    # Initialize scrapers based on user selection
    scrapers = []
    
    if 'all' in args.scrapers:
        scrapers = [
            OzCruisingScraper(),
            RoyalCaribbeanScraper(),
            CarnivalScraper()
        ]
    else:
        if 'ozcruising' in args.scrapers:
            scrapers.append(OzCruisingScraper())
        if 'royal' in args.scrapers:
            scrapers.append(RoyalCaribbeanScraper())
        if 'carnival' in args.scrapers:
            scrapers.append(CarnivalScraper())
    
    # Run scrapers
    all_deals = []
    good_deals = []
    
    for scraper in scrapers:
        try:
            deals = scraper.scrape()
            all_deals.extend(deals)
            
            # Filter for good deals
            scraper_good_deals = scraper.get_good_deals(args.threshold)
            good_deals.extend(scraper_good_deals)
            
            print(f"  └─ {scraper.name}: {len(deals)} total deals, {len(scraper_good_deals)} under ${args.threshold}/day")
            
        except Exception as e:
            print(f"❌ Error running {scraper.name}: {e}")
            continue
    
    print("\n" + "="*80)
    print(f"📊 SUMMARY")
    print("="*80)
    print(f"Total deals scraped: {len(all_deals)}")
    print(f"Deals under ${args.threshold}/day: {len(good_deals)}")
    print("="*80)
    
    # Send alerts
    if good_deals:
        AlertSystem.send_console_alert(good_deals)
        
        if args.email:
            AlertSystem.send_email_alert(good_deals)
        
        if args.save:
            AlertSystem.save_to_file(good_deals, args.output)
    else:
        print("\n" + "="*80)
        print("ℹ️  No deals found under the threshold")
        print("💡 Try increasing the threshold or check back later")
        print("="*80)
    
    print(f"\n✅ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return 0 if good_deals else 1


if __name__ == "__main__":
    sys.exit(main())

