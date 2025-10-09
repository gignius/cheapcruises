"""Background job scheduler for running scrapers"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import asyncio

from config_settings import settings
from database_async import AsyncSessionLocal, CruiseDealRepository, PromoCodeRepository
from scrapers import OzCruisingScraper
from promo_codes import PromoCodeDatabase

# Global scheduler instance
scheduler = AsyncIOScheduler()


def safe_print(text):
    """Print with Unicode error handling"""
    try:
        print(text)
    except UnicodeEncodeError:
        ascii_text = text.encode('ascii', 'ignore').decode('ascii')
        print(ascii_text if ascii_text else "[Output contains unsupported characters]")


async def run_cruise_scrapers():
    """Run all cruise scrapers and save to database"""
    safe_print(f"\n{'='*80}")
    safe_print(f"🤖 AUTOMATED SCRAPER RUN - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    safe_print(f"{'='*80}")
    
    try:
        # Initialize scrapers
        scrapers = [
            # ONLY OzCruising (single data source, simple and reliable)
            OzCruisingScraper(),  # All 11 cruise lines from one aggregator
        ]
        
        all_deals = []
        
        # Run each scraper
        for scraper in scrapers:
            try:
                safe_print(f"\n🔍 Running {scraper.name}...")
                deals = scraper.scrape()
                all_deals.extend(deals)
                safe_print(f"✅ {scraper.name}: Found {len(deals)} deals")
            except Exception as e:
                safe_print(f"❌ Error with {scraper.name}: {e}")
        
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
                        safe_print(f"⚠️  Error saving deal: {e}")
                
                await session.commit()
                safe_print(f"\n💾 Saved {saved_count}/{len(all_deals)} deals to database")
                
                # Deactivate old deals
                deactivated = await repo.deactivate_old_deals(days=7)
                if deactivated > 0:
                    await session.commit()
                    safe_print(f"🗑️  Marked {deactivated} old deals as inactive")
        
        safe_print(f"\n{'='*80}")
        safe_print(f"✅ SCRAPER RUN COMPLETED")
        safe_print(f"{'='*80}\n")
        
    except Exception as e:
        safe_print(f"❌ Error in scraper job: {e}")
        import traceback
        traceback.print_exc()


async def update_promo_codes():
    """Update promo codes from database"""
    safe_print(f"\n📋 Updating promo codes - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Initialize known promo codes
        promo_db = PromoCodeDatabase()
        
        async with AsyncSessionLocal() as session:
            repo = PromoCodeRepository(session)
            
            # Save/update all known codes
            for promo_code in promo_db.get_all_codes():
                await repo.create_or_update(promo_code)
            
            await session.commit()
            safe_print(f"✅ Updated {len(promo_db.get_all_codes())} promo codes")
    
    except Exception as e:
        safe_print(f"❌ Error updating promo codes: {e}")


def start_scheduler():
    """Start the background scheduler"""
    try:
        # Schedule scraper to run every 6 hours (4 times daily)
        scheduler.add_job(
            run_cruise_scrapers,
            'interval',
            hours=settings.scraper_interval_hours,
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
        
        # Optional: Run immediately on startup (for testing)
        # scheduler.add_job(
        #     run_cruise_scrapers,
        #     'date',
        #     run_date=datetime.now(),
        #     id='initial_scrape'
        # )
        
        scheduler.start()
        safe_print(f"✅ Scheduler started - scrapers will run daily at {settings.scraper_schedule_hour}:00")
        
    except Exception as e:
        safe_print(f"❌ Error starting scheduler: {e}")


def stop_scheduler():
    """Stop the background scheduler"""
    try:
        if scheduler.running:
            scheduler.shutdown()
            safe_print("✅ Scheduler stopped")
    except Exception as e:
        safe_print(f"❌ Error stopping scheduler: {e}")


async def run_scrapers_now():
    """Manually trigger scrapers (useful for testing)"""
    await run_cruise_scrapers()
    await update_promo_codes()


