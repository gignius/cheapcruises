"""Extract route map images specifically from OzCruising cruise pages"""
import asyncio
from playwright.async_api import async_playwright
from database_async import AsyncSessionLocal, CruiseDealRepository
from datetime import datetime


async def extract_ozcruising_image(url: str) -> str:
    """Extract route map image from OzCruising cruise detail page"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto(url, wait_until='domcontentloaded', timeout=20000)
            await page.wait_for_timeout(2000)
            
            # Extract route/itinerary image from OzCruising
            image_url = await page.evaluate("""() => {
                // Look for specific OzCruising image patterns
                const selectors = [
                    'img[alt*="map"]',
                    'img[alt*="route"]',
                    'img[alt*="itinerary"]',
                    'img[src*="/cruise/"]',
                    'img[src*="itinerary"]',
                    '.cruise-image img',
                    '.itinerary-image img',
                    '#cruise-map img'
                ];
                
                for (const selector of selectors) {
                    const img = document.querySelector(selector);
                    if (img && img.src && img.src.includes('ozcruising') && !img.src.includes('logo')) {
                        return img.src;
                    }
                }
                
                // Find the main cruise image (usually the largest image)
                const allImages = Array.from(document.querySelectorAll('img'));
                const cruiseImages = allImages.filter(img => 
                    img.src && 
                    img.src.includes('ozcruising') &&
                    !img.src.includes('logo') &&
                    !img.src.includes('icon') &&
                    !img.src.includes('flag') &&
                    img.naturalWidth > 300
                );
                
                if (cruiseImages.length > 0) {
                    // Sort by size and return the largest
                    cruiseImages.sort((a, b) => 
                        (b.naturalWidth * b.naturalHeight) - (a.naturalWidth * a.naturalHeight)
                    );
                    return cruiseImages[0].src;
                }
                
                return null;
            }""")
            
            await browser.close()
            return image_url
            
    except Exception as e:
        print(f"  Error: {str(e)[:50]}")
        return None


async def deep_scrape_ozcruising_images(batch_size: int = 25, max_deals: int = None):
    """Extract route map images from OzCruising cruise pages"""
    print("="*80)
    print("OZCRUISING ROUTE MAP SCRAPER")
    print("="*80)
    print(f"Start: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    async with AsyncSessionLocal() as session:
        repo = CruiseDealRepository(session)
        
        # Get all OzCruising deals without images
        all_deals = await repo.get_all()
        deals_to_update = [
            d for d in all_deals 
            if 'ozcruising.com.au' in d.url and not d.image_url
        ]
        
        if max_deals:
            deals_to_update = deals_to_update[:max_deals]
        
        total = len(deals_to_update)
        print(f"OzCruising deals without images: {total}")
        print(f"Estimated time: {(total * 4 / 60):.1f} minutes")
        print()
        
        updated = 0
        
        for i in range(0, total, batch_size):
            batch = deals_to_update[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total + batch_size - 1) // batch_size
            
            print(f"\nBatch {batch_num}/{total_batches}")
            print("-" * 80)
            
            for idx, deal in enumerate(batch):
                progress = i + idx + 1
                print(f"  [{progress}/{total}] {deal.cruise_line} - {deal.ship_name[:30]}")
                
                try:
                    image_url = await extract_ozcruising_image(deal.url)
                    
                    if image_url:
                        deal.image_url = image_url
                        updated += 1
                        print(f"    [OK] {image_url[:60]}...")
                    else:
                        print(f"    [SKIP] No image")
                    
                    await asyncio.sleep(0.3)  # Be polite
                    
                except Exception as e:
                    print(f"    [ERROR] {str(e)[:50]}")
            
            # Save after each batch
            await session.commit()
            print(f"  Saved: {updated} images so far")
        
        print("\n" + "="*80)
        print(f"COMPLETED: {updated}/{total} images extracted")
        print(f"End: {datetime.now().strftime('%H:%M:%S')}")
        print("="*80)


if __name__ == "__main__":
    # Scrape ALL deals (remove max_deals limit)
    asyncio.run(deep_scrape_ozcruising_images(batch_size=25, max_deals=None))

