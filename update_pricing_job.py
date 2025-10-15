"""Job to update all deals with 2-person and 4-person interior pricing"""
import asyncio
from pricing_scraper import PricingScraper
from database_async import AsyncSessionLocal, CruiseDealRepository
from loguru import logger


async def update_all_pricing():
    """Update pricing for all active deals"""
    logger.info("Starting pricing update job...")
    
    async with AsyncSessionLocal() as session:
        repo = CruiseDealRepository(session)
        
        # Get all active deals
        deals = await repo.get_all()
        active_deals = [d for d in deals if d.is_active]
        
        logger.info(f"Found {len(active_deals)} active deals to update")
        
        # Create pricing scraper
        with PricingScraper(headless=True) as scraper:
            updated_count = 0
            
            for idx, deal in enumerate(active_deals, 1):
                try:
                    if not deal.url:
                        logger.debug(f"Skipping deal {deal.id} - no URL")
                        continue
                    
                    logger.info(f"[{idx}/{len(active_deals)}] Updating pricing for: {deal.ship_name}")
                    
                    # Get pricing
                    price_2p, price_4p = scraper.get_pricing(deal.url)
                    
                    if price_2p or price_4p:
                        # Update the deal
                        deal.price_2p_interior = price_2p
                        deal.price_4p_interior = price_4p
                        updated_count += 1
                        
                        logger.success(f"Updated {deal.ship_name}: 2p=${price_2p}, 4p=${price_4p}")
                    else:
                        logger.warning(f"No pricing found for {deal.ship_name}")
                    
                    # Commit every 10 deals to avoid losing progress
                    if idx % 10 == 0:
                        await session.commit()
                        logger.info(f"Progress: {idx}/{len(active_deals)} deals processed")
                    
                except Exception as e:
                    logger.error(f"Error updating pricing for deal {deal.id}: {e}")
                    continue
            
            # Final commit
            await session.commit()
            logger.success(f"Pricing update completed! Updated {updated_count}/{len(active_deals)} deals")


if __name__ == "__main__":
    asyncio.run(update_all_pricing())
