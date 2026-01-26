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
    scraper_interval_hours: int = 1  # Run scrapers every hour
    
    # Email (Optional)
    email_enabled: bool = False
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    sender_email: Optional[str] = None
    sender_password: Optional[str] = None
    recipient_email: Optional[str] = None
    
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    
    # Security
    secret_key: Optional[str] = None
    
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60
    
    redis_url: str = "redis://localhost:6379/0"
    redis_enabled: bool = False
    
    sentry_dsn: Optional[str] = None
    sentry_enabled: bool = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.secret_key:
            import secrets
            self.secret_key = secrets.token_hex(32)
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4


# Global settings instance
settings = Settings()


