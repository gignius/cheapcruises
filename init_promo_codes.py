"""Initialize promo codes in database"""
import asyncio
import sys
from database_async import AsyncSessionLocal, PromoCodeRepository
from promo_codes import PromoCodeDatabase


def safe_print(text):
    """Print with Unicode error handling"""
    try:
        print(text)
    except UnicodeEncodeError:
        # Fallback to ASCII-safe version
        ascii_text = text.encode('ascii', 'ignore').decode('ascii')
        print(ascii_text if ascii_text else text.encode('unicode_escape').decode('ascii'))


async def init_promo_codes():
    """Initialize known promo codes in database"""
    safe_print("🔄 Initializing promo codes...")
    
    # Get known promo codes
    promo_db = PromoCodeDatabase()
    codes = promo_db.get_all_codes()
    
    # Save to database
    async with AsyncSessionLocal() as session:
        repo = PromoCodeRepository(session)
        
        for code in codes:
            await repo.create_or_update(code)
            safe_print(f"  ✓ Added: {code.code} ({code.cruise_line})")
        
        await session.commit()
    
    safe_print(f"✅ Initialized {len(codes)} promo codes")


if __name__ == "__main__":
    asyncio.run(init_promo_codes())


