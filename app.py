"""Main FastAPI application"""
from fastapi import FastAPI, Request, Depends, Query, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, validator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List

from config_settings import settings
from database_async import init_db, get_db, CruiseDealRepository, PromoCodeRepository
from db_models import CruiseDealDB, PromoCodeDB
from scheduler import start_scheduler, stop_scheduler
import os


class PromoCodeSubmit(BaseModel):
    """Model for user-submitted promo code"""
    code: str = Field(..., min_length=2, max_length=50, description="Promo code")
    cruise_line: str = Field(..., min_length=2, max_length=100, description="Cruise line name")
    description: str = Field(..., min_length=5, max_length=500, description="Code description")
    discount_type: str = Field(default="percentage", description="Type of discount")
    discount_value: Optional[float] = Field(None, ge=0, le=100, description="Discount value")
    conditions: Optional[str] = Field(None, max_length=1000, description="Terms and conditions")
    
    @validator('code')
    def code_must_be_alphanumeric(cls, v):
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Code must be alphanumeric (hyphens and underscores allowed)')
        return v.upper()
    
    @validator('discount_type')
    def discount_type_must_be_valid(cls, v):
        valid_types = ['percentage', 'fixed', 'instant_savings', 'perk']
        if v not in valid_types:
            raise ValueError(f'Discount type must be one of: {valid_types}')
        return v

class VoteType(BaseModel):
    """Model for promo code voting"""
    vote_type: str = Field(..., description="Vote type: 'up' or 'down'")
    
    @validator('vote_type')
    def vote_type_must_be_valid(cls, v):
        if v not in ['up', 'down']:
            raise ValueError("Vote type must be 'up' or 'down'")
        return v


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting CheapCruises.io application")
    try:
        await init_db()
        start_scheduler()
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down application")
    try:
        stop_scheduler()
        logger.info("Shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors"""
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Endpoint not found"}
        )
    return templates.TemplateResponse(
        "404.html",
        {"request": request},
        status_code=404
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {exc}")
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Internal server error"}
        )
    return templates.TemplateResponse(
        "500.html",
        {"request": request},
        status_code=500
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Validation error",
            "errors": exc.errors()
        }
    )

# Create directories if they don't exist
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
os.makedirs("templates", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")


# ============================================================================
# WEB ROUTES (HTML Pages)
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/deals", response_class=HTMLResponse)
async def deals_page(request: Request):
    """Deals listing page"""
    return templates.TemplateResponse("deals.html", {"request": request})


@app.get("/promo-codes", response_class=HTMLResponse)
async def promo_codes_page(request: Request):
    """Promo codes page"""
    return templates.TemplateResponse("promo_codes.html", {"request": request})


@app.get("/cruise/{cruise_id}", response_class=HTMLResponse)
async def cruise_detail_page(request: Request, cruise_id: int):
    """Individual cruise detail page"""
    return templates.TemplateResponse("cruise_detail.html", {
        "request": request,
        "cruise_id": cruise_id
    })


# ============================================================================
# API ROUTES (JSON)
# ============================================================================

@app.get("/api/deals")
async def get_deals(
    max_price_per_day: Optional[float] = Query(None, description="Maximum price per day"),
    cruise_line: Optional[str] = Query(None, description="Filter by cruise line"),
    departure_port: Optional[str] = Query(None, description="Filter by departure port"),
    min_duration: Optional[int] = Query(None, description="Minimum duration in days"),
    max_duration: Optional[int] = Query(None, description="Maximum duration in days"),
    sort_by: str = Query("price_per_day", description="Sort by field"),
    order: str = Query("ASC", description="Sort order (ASC or DESC)"),
    limit: Optional[int] = Query(None, description="Limit number of results"),
    skip: int = Query(0, description="Skip number of results"),
    db: AsyncSession = Depends(get_db)
):
    """Get cruise deals with filters"""
    repo = CruiseDealRepository(db)
    deals = await repo.get_all(
        max_price_per_day=max_price_per_day,
        cruise_line=cruise_line,
        departure_port=departure_port,
        min_duration=min_duration,
        max_duration=max_duration,
        sort_by=sort_by,
        order=order,
        limit=limit,
        skip=skip
    )
    
    return {
        "success": True,
        "count": len(deals),
        "deals": [
            {
                "id": deal.id,
                "cruise_line": deal.cruise_line,
                "ship_name": deal.ship_name,
                "destination": deal.destination,
                "departure_date": deal.departure_date.isoformat() if deal.departure_date else None,
                "duration_days": deal.duration_days,
                "total_price_aud": deal.total_price_aud,
                "price_per_day": deal.price_per_day,
                "cabin_type": deal.cabin_type,
                "departure_port": deal.departure_port,
                "url": deal.url,
                "special_offers": deal.special_offers,
                "image_url": deal.image_url,
                "scraped_at": deal.scraped_at.isoformat(),
            }
            for deal in deals
        ]
    }


@app.get("/api/deals/best")
async def get_best_deals(db: AsyncSession = Depends(get_db)):
    """Get best deals under specific price thresholds"""
    repo = CruiseDealRepository(db)
    
    results = {}
    for threshold in [100, 150, 200]:
        deals = await repo.get_all(
            max_price_per_day=threshold,
            sort_by="price_per_day",
            order="ASC",
            limit=10
        )
        results[f"under_{threshold}"] = [
            {
                "id": deal.id,
                "cruise_line": deal.cruise_line,
                "ship_name": deal.ship_name,
                "destination": deal.destination,
                "departure_date": deal.departure_date.isoformat() if deal.departure_date else None,
                "duration_days": deal.duration_days,
                "total_price_aud": deal.total_price_aud,
                "price_per_day": deal.price_per_day,
                "cabin_type": deal.cabin_type,
                "departure_port": deal.departure_port,
                "url": deal.url,
                "special_offers": deal.special_offers,
                "image_url": deal.image_url,
            }
            for deal in deals
        ]
    
    return {
        "success": True,
        "best_deals": results
    }


@app.get("/api/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get statistics about deals and codes"""
    deal_repo = CruiseDealRepository(db)
    promo_repo = PromoCodeRepository(db)
    
    deal_counts = await deal_repo.count_by_price()
    promo_codes = await promo_repo.get_all()
    valid_codes = len([c for c in promo_codes if c.status == "valid"])
    
    return {
        "success": True,
        "stats": {
            "total_deals": deal_counts["total"],
            "deals_under_100": deal_counts["under_100"],
            "deals_under_150": deal_counts["under_150"],
            "deals_under_200": deal_counts["under_200"],
            "total_promo_codes": len(promo_codes),
            "valid_promo_codes": valid_codes,
            "last_updated": "2025-10-09T00:00:00"
        }
    }


@app.get("/api/promo-codes")
async def get_promo_codes(
    cruise_line: Optional[str] = Query(None, description="Filter by cruise line"),
    valid_only: bool = Query(True, description="Only show valid codes"),
    db: AsyncSession = Depends(get_db)
):
    """Get promo codes with filters"""
    repo = PromoCodeRepository(db)
    codes = await repo.get_all(cruise_line=cruise_line, valid_only=valid_only)
    
    return {
        "success": True,
        "count": len(codes),
        "promo_codes": [
            {
                "id": code.id,
                "code": code.code,
                "cruise_line": code.cruise_line,
                "description": code.description,
                "discount_type": code.discount_type,
                "discount_value": code.discount_value,
                "valid_from": code.valid_from.isoformat() if code.valid_from else None,
                "valid_until": code.valid_until.isoformat() if code.valid_until else None,
                "conditions": code.conditions,
                "source_url": code.source_url,
                "status": code.status,
                "last_validated": code.last_validated.isoformat() if code.last_validated else None,
                "upvotes": code.upvotes,
                "downvotes": code.downvotes,
                "user_submitted": code.user_submitted,
            }
            for code in codes
        ]
    }


@app.get("/api/deals/{deal_id}")
async def get_deal(deal_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single cruise deal by ID"""
    result = await db.execute(
        select(CruiseDealDB).where(CruiseDealDB.id == deal_id)
    )
    deal = result.scalar_one_or_none()
    
    if not deal:
        return {"success": False, "message": "Deal not found"}
    
    return {
        "success": True,
        "deal": {
            "id": deal.id,
            "cruise_line": deal.cruise_line,
            "ship_name": deal.ship_name,
            "destination": deal.destination,
            "departure_date": deal.departure_date.isoformat() if deal.departure_date else None,
            "duration_days": deal.duration_days,
            "total_price_aud": deal.total_price_aud,
            "price_per_day": deal.price_per_day,
            "cabin_type": deal.cabin_type,
            "departure_port": deal.departure_port,
            "url": deal.url,
            "special_offers": deal.special_offers,
            "image_url": deal.image_url,
            "scraped_at": deal.scraped_at.isoformat(),
        }
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": settings.app_version}


@app.post("/api/promo-codes/submit")
async def submit_promo_code(
    promo_data: PromoCodeSubmit,
    db: AsyncSession = Depends(get_db)
):
    """Submit a user promo code with validation"""
    try:
        from promo_codes import PromoCode, PromoCodeStatus
        
        logger.info(f"User submitting promo code: {promo_data.code} for {promo_data.cruise_line}")
        
        # Create promo code object
        promo = PromoCode(
            code=promo_data.code,
            cruise_line=promo_data.cruise_line,
            description=promo_data.description,
            discount_type=promo_data.discount_type,
            discount_value=promo_data.discount_value,
            conditions=promo_data.conditions,
            status=PromoCodeStatus.UNKNOWN,
            last_validated=datetime.now()
        )
        
        # Save to database
        repo = PromoCodeRepository(db)
        db_code = await repo.create_or_update(promo)
        db_code.user_submitted = True
        db_code.upvotes = 0
        db_code.downvotes = 0
        await db.commit()
        
        logger.info(f"Promo code {promo_data.code} submitted successfully")
        return {
            "success": True,
            "message": "Promo code submitted successfully! It will be reviewed.",
            "code": promo_data.code
        }
        
    except Exception as e:
        logger.error(f"Error submitting promo code: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit promo code")


@app.post("/api/promo-codes/{code_id}/vote")
async def vote_promo_code(
    code_id: int,
    vote_data: VoteType,
    db: AsyncSession = Depends(get_db)
):
    """Vote on a promo code (upvote=works, downvote=doesn't work) with validation"""
    try:
        result = await db.execute(
            select(PromoCodeDB).where(PromoCodeDB.id == code_id)
        )
        promo_code = result.scalar_one_or_none()
        
        if not promo_code:
            logger.warning(f"Vote attempt on non-existent promo code: {code_id}")
            raise HTTPException(status_code=404, detail="Promo code not found")
        
        if vote_data.vote_type == "up":
            promo_code.upvotes += 1
            logger.info(f"Upvote for promo code {code_id}: {promo_code.code}")
        else:  # down
            promo_code.downvotes += 1
            logger.info(f"Downvote for promo code {code_id}: {promo_code.code}")
            # If too many downvotes, mark as invalid
            if promo_code.downvotes > 5 and promo_code.downvotes > promo_code.upvotes * 2:
                from promo_codes import PromoCodeStatus
                promo_code.status = PromoCodeStatus.INVALID.value
                logger.warning(f"Promo code {promo_code.code} marked as invalid due to downvotes")
        
        await db.commit()
        
        return {
            "success": True,
            "upvotes": promo_code.upvotes,
            "downvotes": promo_code.downvotes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error voting on promo code {code_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to process vote")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )


