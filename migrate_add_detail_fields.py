"""Add detailed cruise information fields to database"""
import asyncio
from sqlalchemy import text
from database_async import engine

async def migrate():
    """Add new fields to cruise_deals table"""
    
    migrations = [
        "ALTER TABLE cruise_deals ADD COLUMN IF NOT EXISTS cabin_details TEXT",
        "ALTER TABLE cruise_deals ADD COLUMN IF NOT EXISTS itinerary TEXT",
        "ALTER TABLE cruise_deals ADD COLUMN IF NOT EXISTS ship_details TEXT",
        "ALTER TABLE cruise_deals ADD COLUMN IF NOT EXISTS inclusions TEXT"
    ]
    
    async with engine.begin() as conn:
        for migration in migrations:
            print(f"Running: {migration}")
            await conn.execute(text(migration))
    
    print("Migration completed successfully!")

if __name__ == "__main__":
    asyncio.run(migrate())
