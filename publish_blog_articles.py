"""Automated blog article publishing job - publishes 2 articles per day"""
import sys
import asyncio
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from loguru import logger

from db_models import BlogPostDB
from blog_generator import CruiseBlogGenerator
from config_settings import DATABASE_URL

# Configure logging
logger.add("logs/blog_publishing_{time}.log", rotation="1 day", retention="30 days")

async def publish_articles(num_articles: int = 2):
    """Generate and publish blog articles"""
    logger.info(f"Starting blog article publishing job - generating {num_articles} articles")
    
    # Create async engine
    async_url = DATABASE_URL.replace('sqlite:///', 'sqlite+aiosqlite:///')
    engine = create_async_engine(async_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    generator = CruiseBlogGenerator()
    published_count = 0
    
    try:
        async with async_session() as session:
            for i in range(num_articles):
                try:
                    # Generate article
                    article_data = generator.generate_article()
                    
                    # Check if slug already exists
                    result = await session.execute(
                        select(BlogPostDB).where(BlogPostDB.slug == article_data['slug'])
                    )
                    existing = result.scalar_one_or_none()
                    
                    if existing:
                        logger.warning(f"Article with slug '{article_data['slug']}' already exists, skipping")
                        # Try again with a different topic
                        article_data = generator.generate_article()
                    
                    # Create blog post
                    blog_post = BlogPostDB(
                        title=article_data['title'],
                        slug=article_data['slug'],
                        content=article_data['content'],
                        excerpt=article_data['excerpt'],
                        meta_title=article_data['meta_title'],
                        meta_description=article_data['meta_description'],
                        keywords=article_data['keywords'],
                        author=article_data['author'],
                        category=article_data['category'],
                        tags=article_data['tags'],
                        status='published',
                        published_at=datetime.now(),
                        ai_generated=article_data['ai_generated'],
                        generation_prompt=article_data['generation_prompt'],
                    )
                    
                    session.add(blog_post)
                    await session.commit()
                    
                    published_count += 1
                    logger.success(f"Published article {i+1}/{num_articles}: {article_data['title']}")
                    
                except Exception as e:
                    logger.error(f"Error publishing article {i+1}: {e}")
                    await session.rollback()
                    continue
        
        logger.info(f"Blog publishing job completed! Published {published_count}/{num_articles} articles")
        return published_count
        
    except Exception as e:
        logger.error(f"Fatal error in blog publishing job: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    num_articles = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    asyncio.run(publish_articles(num_articles))
