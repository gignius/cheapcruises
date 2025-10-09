"""Application settings using Pydantic Settings"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Application
    app_name: str = "CheapCruises.io"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Database
    database_url: str = "postgresql+asyncpg://cruises:cruises@localhost/cruises"
    database_echo: bool = False  # SQL query logging
    
    # Price Thresholds
    price_threshold: float = 200.0
    
    # Scraping
    user_agent: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    request_timeout: int = 30
    scraper_schedule_hour: int = 6  # Run scrapers at 6 AM daily
    
    # Email (Optional)
    email_enabled: bool = False
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    sender_email: Optional[str] = None
    sender_password: Optional[str] = None
    recipient_email: Optional[str] = None
    
    # Security
    secret_key: str = "change-this-in-production-use-openssl-rand-hex-32"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4


# Global settings instance
settings = Settings()


