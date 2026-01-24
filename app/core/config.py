"""
Application Configuration Settings
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "News AI Generator API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost/news_ai"
    # Local override for development (socket-based proxy)
    DATABASE_URL_LOCAL: str = ""
    
    # External Services
    GEMINI_API_KEY: str = "AIzaSyDSxL4361Hes4FX_TtBO6StJSwsg5JnL3Y"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    # Preferred Gemini model (can be overridden in .env)
    GEMINI_MODEL: str = "gemini-2.5-pro"
    SCRAPEGRAPH_ENDPOINT: str = "http://localhost:8001/api/scrape"
    # Strapi configuration (production/staging)
    STRAPI_URL: str = ""
    STRAPI_TOKEN: str = ""

    # Sportmonks API (nuevo proveedor de fútbol)
    SPORTMONKS_API_TOKEN: str = ""
    SPORTMONKS_BASE_URL: str = "https://api.sportmonks.com/v3/football"
    SPORTMONKS_PREMIER_LEAGUE_ID: int = 8
    SPORTMONKS_PREMIER_SEASON_ID: int = 23614
    SPORTMONKS_SERIEA_LEAGUE_ID: int = 384
    SPORTMONKS_SERIEA_SEASON_ID: int = 23598
    
    # WordPress
    WP_GRAPHQL_ENDPOINT: str = "https://example.com/graphql"
    WP_AUTH_TOKEN: str = ""
    
    # Scraping
    SCRAPE_URLS: str = "https://rpp.pe/deportes,https://depor.com/,https://www.espn.com.pe/"

    # Easypromos integration (opcional)
    EASYPROMOS_API_TOKEN: str = ""
    EASYPROMOS_CAMPAIGN_ID: str = ""
    EASYPROMOS_API_AUTLOGIN: str = ""
    EASYPROMOS_PROMO_BASE: str = ""


    
    # CORS
    CORS_ORIGINS: str = "*"
    # Scraping / Playwright
    # Timeout for page navigation in milliseconds (used by Playwright page.goto)
    SCRAPE_TIMEOUT_MS: int = 180000
    # Comma-separated Chromium launch args for Playwright (useful for Cloud Run)
    PLAYWRIGHT_LAUNCH_ARGS: str = "--no-sandbox,--disable-dev-shm-usage,--disable-setuid-sandbox"
    
    @property
    def scrape_urls_list(self) -> List[str]:
        """Parse SCRAPE_URLS string to list"""
        return [url.strip() for url in self.SCRAPE_URLS.split(",") if url.strip()]
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS string to list"""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def playwright_launch_args_list(self) -> List[str]:
        """Parse PLAYWRIGHT_LAUNCH_ARGS into a list suitable for Playwright's `args` param"""
        raw = (self.PLAYWRIGHT_LAUNCH_ARGS or "").strip()
        if not raw:
            return []
        return [a.strip() for a in raw.split(',') if a.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


# Singleton instance
settings = Settings()
