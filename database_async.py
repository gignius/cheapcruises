"""Async database connection and session management"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, func
from db_models import Base, CruiseDealDB, PromoCodeDB
from config_settings import settings
from datetime import datetime
from models import CruiseDeal
from promo_codes import PromoCode, PromoCodeStatus
import json


# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    future=True
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        print("✅ Database tables created")
    except UnicodeEncodeError:
        print("[OK] Database tables created")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


class CruiseDealRepository:
    """Repository for cruise deal operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def find_existing(self, deal: CruiseDeal) -> CruiseDealDB:
        """Find if a similar deal already exists"""
        result = await self.session.execute(
            select(CruiseDealDB)
            .where(CruiseDealDB.cruise_line == deal.cruise_line)
            .where(CruiseDealDB.ship_name == deal.ship_name)
            .where(CruiseDealDB.destination == deal.destination)
            .where(CruiseDealDB.departure_date == deal.departure_date)
            .where(CruiseDealDB.duration_days == deal.duration_days)
            .where(CruiseDealDB.departure_port == deal.departure_port)
            .where(CruiseDealDB.is_active == True)
        )
        return result.scalar_one_or_none()
    
    async def create(self, deal: CruiseDeal) -> CruiseDealDB:
        """Create a new cruise deal or update existing"""
        # Check if deal already exists
        existing = await self.find_existing(deal)
        
        if existing:
            # Update existing deal
            existing.total_price_aud = deal.total_price_aud
            existing.price_per_day = deal.price_per_day
            existing.cabin_type = deal.cabin_type
            existing.url = deal.url
            existing.special_offers = deal.special_offers
            existing.image_url = deal.image_url if hasattr(deal, 'image_url') else existing.image_url
            existing.last_updated = datetime.now()
            existing.scraped_at = deal.scraped_at
            await self.session.flush()
            return existing
        
        # Create new deal
        db_deal = CruiseDealDB(
            cruise_line=deal.cruise_line,
            ship_name=deal.ship_name,
            destination=deal.destination,
            departure_date=deal.departure_date,
            duration_days=deal.duration_days,
            total_price_aud=deal.total_price_aud,
            price_per_day=deal.price_per_day,
            cabin_type=deal.cabin_type,
            departure_port=deal.departure_port,
            url=deal.url,
            special_offers=deal.special_offers,
            image_url=deal.image_url if hasattr(deal, 'image_url') else None,
            scraped_at=deal.scraped_at,
            last_updated=datetime.now(),
            is_active=True
        )
        self.session.add(db_deal)
        await self.session.flush()
        return db_deal
    
    async def get_all(
        self,
        max_price_per_day: float = None,
        cruise_line: str = None,
        departure_port: str = None,
        min_duration: int = None,
        max_duration: int = None,
        sort_by: str = "price_per_day",
        order: str = "ASC",
        limit: int = None,
        skip: int = 0
    ):
        """Get all deals with filters"""
        query = select(CruiseDealDB).where(CruiseDealDB.is_active == True)
        
        if max_price_per_day:
            query = query.where(CruiseDealDB.price_per_day <= max_price_per_day)
        
        if cruise_line:
            query = query.where(CruiseDealDB.cruise_line.ilike(f"%{cruise_line}%"))
        
        if departure_port:
            query = query.where(CruiseDealDB.departure_port.ilike(f"%{departure_port}%"))
        
        if min_duration:
            query = query.where(CruiseDealDB.duration_days >= min_duration)
        
        if max_duration:
            query = query.where(CruiseDealDB.duration_days <= max_duration)
        
        # Sorting
        sort_column = getattr(CruiseDealDB, sort_by, CruiseDealDB.price_per_day)
        if order.upper() == "DESC":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        if skip:
            query = query.offset(skip)
        
        if limit:
            query = query.limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def count_by_price(self):
        """Get count of deals by price thresholds"""
        total = await self.session.scalar(
            select(func.count()).select_from(CruiseDealDB).where(CruiseDealDB.is_active == True)
        )
        
        under_100 = await self.session.scalar(
            select(func.count()).select_from(CruiseDealDB)
            .where(CruiseDealDB.is_active == True)
            .where(CruiseDealDB.price_per_day <= 100)
        )
        
        under_150 = await self.session.scalar(
            select(func.count()).select_from(CruiseDealDB)
            .where(CruiseDealDB.is_active == True)
            .where(CruiseDealDB.price_per_day <= 150)
        )
        
        under_200 = await self.session.scalar(
            select(func.count()).select_from(CruiseDealDB)
            .where(CruiseDealDB.is_active == True)
            .where(CruiseDealDB.price_per_day <= 200)
        )
        
        return {
            "total": total or 0,
            "under_100": under_100 or 0,
            "under_150": under_150 or 0,
            "under_200": under_200 or 0
        }
    
    async def deactivate_old_deals(self, days: int = 7):
        """Mark old deals as inactive"""
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        cutoff_date = datetime.fromtimestamp(cutoff)
        
        result = await self.session.execute(
            select(CruiseDealDB)
            .where(CruiseDealDB.last_updated < cutoff_date)
            .where(CruiseDealDB.is_active == True)
        )
        deals = result.scalars().all()
        
        for deal in deals:
            deal.is_active = False
        
        return len(deals)


class PromoCodeRepository:
    """Repository for promo code operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_or_update(self, promo_code: PromoCode) -> PromoCodeDB:
        """Create or update a promo code"""
        # Check if exists
        result = await self.session.execute(
            select(PromoCodeDB)
            .where(PromoCodeDB.code == promo_code.code)
            .where(PromoCodeDB.cruise_line == promo_code.cruise_line)
        )
        db_code = result.scalar_one_or_none()
        
        if db_code:
            # Update existing
            db_code.description = promo_code.description
            db_code.discount_type = promo_code.discount_type
            db_code.discount_value = promo_code.discount_value
            db_code.valid_from = promo_code.valid_from
            db_code.valid_until = promo_code.valid_until
            db_code.conditions = promo_code.conditions
            db_code.source_url = promo_code.source_url
            db_code.status = promo_code.status.value
            db_code.last_validated = promo_code.last_validated
            db_code.combinable_with = json.dumps(promo_code.combinable_with) if promo_code.combinable_with else None
            db_code.updated_at = datetime.now()
        else:
            # Create new
            db_code = PromoCodeDB(
                code=promo_code.code,
                cruise_line=promo_code.cruise_line,
                description=promo_code.description,
                discount_type=promo_code.discount_type,
                discount_value=promo_code.discount_value,
                valid_from=promo_code.valid_from,
                valid_until=promo_code.valid_until,
                conditions=promo_code.conditions,
                source_url=promo_code.source_url,
                status=promo_code.status.value,
                last_validated=promo_code.last_validated,
                combinable_with=json.dumps(promo_code.combinable_with) if promo_code.combinable_with else None
            )
            self.session.add(db_code)
        
        await self.session.flush()
        return db_code
    
    async def get_all(self, cruise_line: str = None, valid_only: bool = False):
        """Get all promo codes with filters"""
        query = select(PromoCodeDB)
        
        if cruise_line:
            query = query.where(PromoCodeDB.cruise_line.ilike(f"%{cruise_line}%"))
        
        if valid_only:
            query = query.where(PromoCodeDB.status == PromoCodeStatus.VALID.value)
        
        result = await self.session.execute(query)
        return result.scalars().all()


