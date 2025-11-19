"""Generate 1000 blog articles with images in batches"""
import asyncio
import sys
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from loguru import logger

from db_models import BlogPostDB
from blog_generator import CruiseBlogGenerator
from config_settings import settings

# Configure logging
logger.add("logs/blog_generation_{time}.log", rotation="100 MB", retention="30 days")

async def generate_articles_batch(target_count: int = 1000, batch_size: int = 10):
    """Generate blog articles in batches to avoid memory issues"""
    logger.info(f"Starting blog article generation - target: {target_count} articles")
    
    # Create async engine
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    generator = CruiseBlogGenerator(generate_images=True)
    total_published = 0
    total_attempts = 0
    
    try:
        async with async_session() as session:
            result = await session.execute(select(func.count(BlogPostDB.id)))
            current_count = result.scalar()
            logger.info(f"Current blog posts in database: {current_count}")
            
            remaining = target_count - current_count
            if remaining <= 0:
                logger.info(f"Target already reached! {current_count} articles exist.")
                return current_count
            
            logger.info(f"Need to generate {remaining} more articles")
            
            batch_num = 0
            while total_published < remaining:
                batch_num += 1
                batch_start = total_published
                batch_end = min(total_published + batch_size, remaining)
                
                logger.info(f"=== Batch {batch_num}: Generating articles {batch_start+1} to {batch_end} ===")
                
                for i in range(batch_start, batch_end):
                    total_attempts += 1
                    try:
                        # Generate article
                        logger.info(f"Generating article {i+1}/{remaining} (attempt {total_attempts})")
                        article_data = generator.generate_article()
                        
                        # Check if slug already exists
                        result = await session.execute(
                            select(BlogPostDB).where(BlogPostDB.slug == article_data['slug'])
                        )
                        existing = result.scalar_one_or_none()
                        
                        if existing:
                            logger.warning(f"Article with slug '{article_data['slug']}' already exists, regenerating")
                            # Try again with a different topic
                            article_data = generator.generate_article()
                            
                            result = await session.execute(
                                select(BlogPostDB).where(BlogPostDB.slug == article_data['slug'])
                            )
                            existing = result.scalar_one_or_none()
                            
                            if existing:
                                logger.error(f"Duplicate slug again: '{article_data['slug']}', skipping")
                                continue
                        
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
                            featured_image_url=article_data.get('featured_image_url'),
                            featured_image_alt=article_data.get('featured_image_alt'),
                            status='published',
                            published_at=datetime.now(),
                            ai_generated=article_data['ai_generated'],
                            generation_prompt=article_data['generation_prompt'],
                        )
                        
                        session.add(blog_post)
                        await session.commit()
                        
                        total_published += 1
                        logger.success(f"Published article {total_published}/{remaining}: {article_data['title']}")
                        
                    except Exception as e:
                        logger.error(f"Error publishing article {i+1}: {e}")
                        await session.rollback()
                        continue
                
                logger.info(f"Batch {batch_num} completed. Total published: {total_published}/{remaining}")
                
                if total_published < remaining:
                    logger.info("Waiting 5 seconds before next batch...")
                    await asyncio.sleep(5)
        
        final_count = current_count + total_published
        logger.info(f"Blog generation completed! Published {total_published} new articles. Total: {final_count}")
        return final_count
        
    except Exception as e:
        logger.error(f"Fatal error in blog generation: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    target = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    logger.info(f"Starting generation: target={target}, batch_size={batch_size}")
    final_count = asyncio.run(generate_articles_batch(target, batch_size))
    logger.info(f"Final article count: {final_count}")
