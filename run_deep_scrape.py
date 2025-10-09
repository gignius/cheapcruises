"""Run the deep image scraper to get route maps"""
import asyncio
import sys

# Import the deep scraper
from deep_image_scraper import deep_scrape_images

async def main():
    """Run deep scrape with options"""
    print("="*80)
    print("DEEP IMAGE SCRAPER")
    print("="*80)
    print()
    print("This will visit individual cruise pages to extract route map images.")
    print("This process takes time (~5 seconds per cruise page).")
    print()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--test':
            print("TEST MODE: Scraping first 50 deals only")
            await deep_scrape_images(batch_size=10, max_deals=50)
        elif sys.argv[1] == '--full':
            print("FULL MODE: Scraping ALL deals (this will take 2-3 hours)")
            response = input("Are you sure? Type 'yes' to continue: ")
            if response.lower() == 'yes':
                await deep_scrape_images(batch_size=50, max_deals=None)
            else:
                print("Cancelled.")
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Usage:")
            print("  python run_deep_scrape.py --test     (scrape first 50 deals)")
            print("  python run_deep_scrape.py --full     (scrape all deals, 2-3 hours)")
    else:
        # Default: scrape 100 deals
        print("DEFAULT MODE: Scraping first 100 deals")
        print("(Use --test for 50 deals, --full for all deals)")
        print()
        await deep_scrape_images(batch_size=25, max_deals=100)

if __name__ == "__main__":
    asyncio.run(main())

