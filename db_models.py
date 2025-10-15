"""SQLAlchemy database models"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, Integer, DateTime, Boolean, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


class CruiseDealDB(Base):
    """Cruise deal database model"""
    __tablename__ = "cruise_deals"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cruise_line: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    ship_name: Mapped[str] = mapped_column(String(100), nullable=False)
    destination: Mapped[Optional[str]] = mapped_column(String(200))
    departure_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    duration_days: Mapped[int] = mapped_column(Integer)
    total_price_aud: Mapped[float] = mapped_column(Float, nullable=False)
    price_per_day: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    cabin_type: Mapped[Optional[str]] = mapped_column(String(50))
    departure_port: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    url: Mapped[Optional[str]] = mapped_column(String(500))
    special_offers: Mapped[Optional[str]] = mapped_column(Text)
    image_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    price_2p_interior: Mapped[Optional[float]] = mapped_column(Float)  # Total price for 2 people in interior cabin
    price_4p_interior: Mapped[Optional[float]] = mapped_column(Float)  # Total price for 4 people in interior cabin
    
    cabin_details: Mapped[Optional[str]] = mapped_column(Text)  # JSON: [{category, type, price_pp, total_price, available}]
    itinerary: Mapped[Optional[str]] = mapped_column(Text)  # JSON: [{port, arrival, departure, description}]
    ship_details: Mapped[Optional[str]] = mapped_column(Text)  # JSON: {tonnage, capacity, year_built, amenities}
    inclusions: Mapped[Optional[str]] = mapped_column(Text)  # JSON: [list of included items]
    
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    def __repr__(self):
        return f"<CruiseDeal {self.cruise_line} - {self.ship_name} - ${self.price_per_day}/day>"


class PromoCodeDB(Base):
    """Promo code database model"""
    __tablename__ = "promo_codes"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    cruise_line: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    discount_type: Mapped[str] = mapped_column(String(50))  # percentage, fixed, instant_savings
    discount_value: Mapped[Optional[float]] = mapped_column(Float)
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime)
    conditions: Mapped[Optional[str]] = mapped_column(Text)
    source_url: Mapped[Optional[str]] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(50), index=True)  # valid, expired, invalid, unknown
    last_validated: Mapped[Optional[datetime]] = mapped_column(DateTime)
    combinable_with: Mapped[Optional[str]] = mapped_column(Text)  # JSON string
    
    # User feedback fields
    upvotes: Mapped[int] = mapped_column(Integer, default=0)
    downvotes: Mapped[int] = mapped_column(Integer, default=0)
    user_submitted: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<PromoCode {self.code} - {self.cruise_line} - {self.status}>"


