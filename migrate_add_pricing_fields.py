"""Add price_2p_interior and price_4p_interior fields to cruise_deals table"""
import asyncio
from sqlalchemy import text
from database_async import engine
from loguru import logger


async def migrate():
    """Add new pricing fields to the database"""
    async with engine.begin() as conn:
        try:
            # Add price_2p_interior column
            await conn.execute(text("""
                ALTER TABLE cruise_deals 
                ADD COLUMN IF NOT EXISTS price_2p_interior FLOAT;
            """))
            logger.info("Added price_2p_interior column")
            
            # Add price_4p_interior column
            await conn.execute(text("""
                ALTER TABLE cruise_deals 
                ADD COLUMN IF NOT EXISTS price_4p_interior FLOAT;
            """))
            logger.info("Added price_4p_interior column")
            
            logger.success("Migration completed successfully!")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(migrate())
