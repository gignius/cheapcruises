"""Background job scheduler for running scrapers"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import asyncio
from loguru import logger

from config_settings import settings
from database_async import AsyncSessionLocal, CruiseDealRepository, PromoCodeRepository
from scrapers import OzCruisingScraper
from promo_codes import PromoCodeDatabase

# Global scheduler instance
scheduler = AsyncIOScheduler()


async def run_cruise_scrapers():
    """Run all cruise scrapers and save to database"""
    logger.info("="*80)
    logger.info("Starting automated scraper run")
    logger.info("="*80)
    
    try:
        # Initialize scrapers
        scrapers = [
            OzCruisingScraper(),  # All 11 cruise lines from one aggregator
        ]
        
        all_deals = []
        
        # Run each scraper
        for scraper in scrapers:
            try:
                logger.info(f"Running scraper: {scraper.name}")
                deals = scraper.scrape()
                all_deals.extend(deals)
                logger.success(f"{scraper.name}: Found {len(deals)} deals")
            except Exception as e:
                logger.error(f"Error with {scraper.name}: {e}", exc_info=True)
        
        # Save to database
        if all_deals:
            async with AsyncSessionLocal() as session:
                repo = CruiseDealRepository(session)
                
                saved_count = 0
                for deal in all_deals:
                    try:
                        await repo.create(deal)
                        saved_count += 1
                    except Exception as e:
                        logger.warning(f"Error saving deal: {e}")
                
                await session.commit()
                logger.info(f"Saved {saved_count}/{len(all_deals)} deals to database")
                
                # Deactivate old deals
                deactivated = await repo.deactivate_old_deals(days=7)
                if deactivated > 0:
                    await session.commit()
                    logger.info(f"Marked {deactivated} old deals as inactive")
        else:
            logger.warning("No deals found during scraper run")
        
        logger.info("="*80)
        logger.success("Scraper run completed successfully")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"Critical error in scraper job: {e}", exc_info=True)


async def update_promo_codes():
    """Update promo codes from database"""
    logger.info("Starting promo code update")
    
    try:
        # Initialize known promo codes
        promo_db = PromoCodeDatabase()
        
        async with AsyncSessionLocal() as session:
            repo = PromoCodeRepository(session)
            
            # Save/update all known codes
            codes = promo_db.get_all_codes()
            for promo_code in codes:
                await repo.create_or_update(promo_code)
            
            await session.commit()
            logger.success(f"Updated {len(codes)} promo codes")
    
    except Exception as e:
        logger.error(f"Error updating promo codes: {e}", exc_info=True)


def start_scheduler():
    """Start the background scheduler"""
    try:
        # Schedule scraper to run every 6 hours (4 times daily)
        scraper_hours = getattr(settings, 'scraper_interval_hours', 6)  # Default to 6 if not found
        
        scheduler.add_job(
            run_cruise_scrapers,
            'interval',
            hours=scraper_hours,
            id='cruise_scraper',
            name='Run cruise scrapers every 6 hours',
            replace_existing=True,
            next_run_time=None  # Start immediately on app start
        )
        
        # Schedule promo code update every 12 hours
        scheduler.add_job(
            update_promo_codes,
            'interval',
            hours=12,
            id='promo_code_updater',
            name='Update promo codes every 12 hours',
            replace_existing=True
        )
        
        scheduler.start()
        logger.info(f"Scheduler started - scrapers run every {scraper_hours} hours, promo codes every 12 hours")
        
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}", exc_info=True)


def stop_scheduler():
    """Stop the background scheduler"""
    try:
        if scheduler.running:
            scheduler.shutdown()
            logger.info("Scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")


async def run_scrapers_now():
    """Manually trigger scrapers (useful for testing)"""
    await run_cruise_scrapers()
    await update_promo_codes()


