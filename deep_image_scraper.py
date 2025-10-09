"""Deep scraper to extract route map images from individual cruise pages"""
import asyncio
from playwright.async_api import async_playwright
from database_async import AsyncSessionLocal, CruiseDealRepository
from datetime import datetime
import re


async def extract_route_image_from_page(url: str, cruise_line: str) -> str:
    """Extract route/map image from a cruise detail page"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Load the page
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(3000)
            
            # Extract images based on cruise line
            image_url = None
            
            if 'carnival.com' in url:
                # Carnival: Look for itinerary map or route images
                image_url = await page.evaluate("""() => {
                    const selectors = [
                        'img[alt*="map"]',
                        'img[alt*="itinerary"]',
                        'img[alt*="route"]',
                        'img[src*="itinerary"]',
                        'img[src*="map"]',
                        '.itinerary-map img',
                        '.route-map img'
                    ];
                    
                    for (const selector of selectors) {
                        const img = document.querySelector(selector);
                        if (img && img.src) return img.src;
                    }
                    
                    // Fallback: largest image on page
                    const images = Array.from(document.querySelectorAll('img'));
                    const large = images.find(img => img.naturalWidth > 400 && img.naturalHeight > 300);
                    return large ? large.src : null;
                }""")
            
            elif 'royalcaribbean.com' in url:
                # Royal Caribbean: route/itinerary images
                image_url = await page.evaluate("""() => {
                    const selectors = [
                        'img[alt*="map"]',
                        'img[alt*="route"]',
                        'img[alt*="itinerary"]',
                        '[class*="map"] img',
                        '[class*="route"] img',
                        '[class*="itinerary"] img'
                    ];
                    
                    for (const selector of selectors) {
                        const img = document.querySelector(selector);
                        if (img && img.src && !img.src.includes('icon')) return img.src;
                    }
                    
                    // Fallback: hero image
                    const hero = document.querySelector('.hero-image img, .main-image img, [class*="hero"] img');
                    return hero ? hero.src : null;
                }""")
            
            elif 'ncl.com' in url:
                # Norwegian: itinerary/map images
                image_url = await page.evaluate("""() => {
                    const selectors = [
                        'img[alt*="map"]',
                        'img[alt*="itinerary"]',
                        'img[src*="map"]',
                        '.itinerary-img img',
                        '.voyage-map img'
                    ];
                    
                    for (const selector of selectors) {
                        const img = document.querySelector(selector);
                        if (img && img.src) return img.src;
                    }
                    
                    return null;
                }""")
            
            elif 'hollandamerica.com' in url:
                # Holland America already has good images from API
                pass
            
            elif 'celebritycruises.com' in url:
                # Celebrity: similar to Royal Caribbean
                image_url = await page.evaluate("""() => {
                    const map = document.querySelector('img[alt*="map"], img[alt*="route"], [class*="map"] img');
                    return map ? map.src : null;
                }""")
            
            elif 'ozcruising.com.au' in url:
                # OzCruising: extract route map from cruise detail page
                image_url = await page.evaluate("""() => {
                    const selectors = [
                        'img[alt*="map"]',
                        'img[alt*="route"]',
                        'img[alt*="itinerary"]',
                        'img[src*="map"]',
                        'img[src*="route"]',
                        '.cruise-map img',
                        '.itinerary-map img'
                    ];
                    
                    for (const selector of selectors) {
                        const img = document.querySelector(selector);
                        if (img && img.src && img.src.includes('ozcruising')) {
                            return img.src;
                        }
                    }
                    
                    // Look for any large image that might be the route
                    const images = Array.from(document.querySelectorAll('img'));
                    const large = images.find(img => 
                        img.naturalWidth > 500 && 
                        img.naturalHeight > 300 &&
                        img.src.includes('ozcruising') &&
                        !img.src.includes('logo')
                    );
                    return large ? large.src : null;
                }""")
            
            await browser.close()
            return image_url
            
    except Exception as e:
        print(f"  Error extracting image from {url[:50]}: {e}")
        return None


async def deep_scrape_images(batch_size: int = 50, max_deals: int = None):
    """Deep scrape to extract route map images"""
    print("="*80)
    print("DEEP IMAGE SCRAPER - Extracting Route Maps from Cruise Pages")
    print("="*80)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    async with AsyncSessionLocal() as session:
        repo = CruiseDealRepository(session)
        
        # Get all deals without images
        all_deals = await repo.get_all()
        deals_without_images = [d for d in all_deals if not d.image_url]
        
        if max_deals:
            deals_without_images = deals_without_images[:max_deals]
        
        total_deals = len(deals_without_images)
        print(f"Deals without images: {total_deals}")
        print(f"Batch size: {batch_size}")
        print(f"Estimated time: {(total_deals * 5 / 60):.1f} minutes")
        print()
        
        updated_count = 0
        
        # Process in batches
        for i in range(0, total_deals, batch_size):
            batch = deals_without_images[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_deals + batch_size - 1) // batch_size
            
            print(f"\nBatch {batch_num}/{total_batches} ({len(batch)} deals)")
            print("-" * 80)
            
            for idx, deal in enumerate(batch):
                try:
                    print(f"  [{i+idx+1}/{total_deals}] {deal.cruise_line} - {deal.ship_name[:30]}")
                    
                    # Extract image from URL
                    image_url = await extract_route_image_from_page(deal.url, deal.cruise_line)
                    
                    if image_url:
                        # Update database
                        deal.image_url = image_url
                        await session.commit()
                        updated_count += 1
                        print(f"    ✅ Image found: {image_url[:60]}...")
                    else:
                        print(f"    ⚠️  No image found")
                    
                    # Small delay to be polite
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    print(f"    ❌ Error: {e}")
                    continue
            
            # Save progress after each batch
            await session.commit()
            print(f"\n  Progress saved: {updated_count}/{i+len(batch)} images extracted")
    
    print("\n" + "="*80)
    print(f"DEEP SCRAPE COMPLETED")
    print(f"Total images extracted: {updated_count}/{total_deals}")
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)


async def main():
    """Run deep image scraping"""
    # For testing, start with just 100 deals
    # Change max_deals=None to scrape all deals
    await deep_scrape_images(batch_size=50, max_deals=100)


if __name__ == "__main__":
    asyncio.run(main())

