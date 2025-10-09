"""Download route map images locally instead of just storing URLs"""
import asyncio
import os
import requests
from pathlib import Path
from playwright.async_api import async_playwright
from database_async import AsyncSessionLocal, CruiseDealRepository
from datetime import datetime


# Create static images directory
IMAGES_DIR = Path("static/images/cruises")
IMAGES_DIR.mkdir(parents=True, exist_ok=True)


async def download_image_from_url(url: str, cruise_id: int) -> str:
    """Download an image and save it locally"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            # Save with cruise ID as filename
            ext = url.split('.')[-1].split('?')[0]  # Get extension
            if ext not in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
                ext = 'jpg'
            
            filename = f"cruise_{cruise_id}.{ext}"
            filepath = IMAGES_DIR / filename
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            # Return relative path for database
            return f"/static/images/cruises/{filename}"
        return None
    except Exception as e:
        print(f"    Error downloading: {e}")
        return None


async def extract_and_download_ozcruising_image(url: str, cruise_id: int) -> str:
    """Extract image from OzCruising page and download it locally"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto(url, wait_until='domcontentloaded', timeout=15000)
            await page.wait_for_timeout(2000)
            
            # Extract image URL
            image_url = await page.evaluate("""() => {
                const selectors = [
                    'img[alt*="map"]',
                    'img[alt*="route"]',
                    'img[src*="cruise"]',
                    '.cruise-image img',
                    'img[src*="static.ozcruising"]'
                ];
                
                for (const selector of selectors) {
                    const img = document.querySelector(selector);
                    if (img && img.src && img.src.includes('ozcruising') && !img.src.includes('logo')) {
                        return img.src;
                    }
                }
                
                // Get largest image
                const allImages = Array.from(document.querySelectorAll('img'));
                const cruiseImages = allImages.filter(img => 
                    img.src && img.src.includes('ozcruising') &&
                    !img.src.includes('logo') && !img.src.includes('icon') &&
                    img.naturalWidth > 300
                );
                
                if (cruiseImages.length > 0) {
                    cruiseImages.sort((a, b) => 
                        (b.naturalWidth * b.naturalHeight) - (a.naturalWidth * a.naturalHeight)
                    );
                    return cruiseImages[0].src;
                }
                
                return null;
            }""")
            
            await browser.close()
            
            if image_url:
                # Download the image locally
                return await download_image_from_url(image_url, cruise_id)
            
            return None
            
    except Exception as e:
        return None


async def download_all_images(batch_size: int = 25, max_deals: int = None):
    """Download all cruise images locally"""
    print("="*80)
    print("DOWNLOADING ROUTE MAP IMAGES LOCALLY")
    print("="*80)
    print(f"Start: {datetime.now().strftime('%H:%M:%S')}")
    print(f"Saving to: {IMAGES_DIR.absolute()}")
    print()
    
    async with AsyncSessionLocal() as session:
        repo = CruiseDealRepository(session)
        
        # Get all deals without local images
        all_deals = await repo.get_all()
        deals_to_update = [
            d for d in all_deals 
            if not d.image_url or not d.image_url.startswith('/static/')
        ]
        
        if max_deals:
            deals_to_update = deals_to_update[:max_deals]
        
        total = len(deals_to_update)
        print(f"Deals to process: {total}")
        print(f"Estimated time: {(total * 4 / 60):.1f} minutes")
        print()
        
        downloaded = 0
        
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
                    # Extract and download image
                    local_path = await extract_and_download_ozcruising_image(deal.url, deal.id)
                    
                    if local_path:
                        deal.image_url = local_path
                        downloaded += 1
                        print(f"    [OK] Saved: {local_path}")
                    else:
                        print(f"    [SKIP] No image")
                    
                    await asyncio.sleep(0.3)
                    
                except Exception as e:
                    print(f"    [ERROR] {str(e)[:50]}")
            
            # Save after each batch
            await session.commit()
            print(f"  Progress: {downloaded} images downloaded")
        
        print("\n" + "="*80)
        print(f"COMPLETED: {downloaded}/{total} images downloaded locally")
        print(f"End: {datetime.now().strftime('%H:%M:%S')}")
        print(f"Images saved to: {IMAGES_DIR.absolute()}")
        print("="*80)


if __name__ == "__main__":
    # Download ALL images locally
    asyncio.run(download_all_images(batch_size=25, max_deals=None))

