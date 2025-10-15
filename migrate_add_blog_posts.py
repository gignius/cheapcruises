"""Migration script to add blog_posts table"""
import sys
from sqlalchemy import create_engine, text
from db_models import Base, BlogPostDB
from config_settings import settings

def create_blog_posts_table():
    """Create blog_posts table"""
    db_url = settings.database_url.replace('+asyncpg', '')
    engine = create_engine(db_url)
    
    # Create table using SQLAlchemy ORM
    Base.metadata.create_all(engine, tables=[BlogPostDB.__table__])
    print("✅ Blog posts table created successfully!")

if __name__ == "__main__":
    create_blog_posts_table()
