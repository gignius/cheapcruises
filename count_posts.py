"""Count blog posts in database"""
import asyncio
from database_async import AsyncSessionLocal
from db_models import BlogPostDB
from sqlalchemy import select, func

async def count_posts():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(func.count(BlogPostDB.id)))
        count = result.scalar()
        print(f'Total blog posts: {count}')
        return count

if __name__ == "__main__":
    asyncio.run(count_posts())
