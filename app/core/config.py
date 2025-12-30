"""
Application Configuration Settings
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # API-SPORTS (Liga Perú)
    API_SPORTS_KEY: str = ""
    API_SPORTS_BASE: str = "https://v3.football.api-sports.io"
    PERU_LEAGUE_ID: int = 281
    PERU_SEASON: int = 2025
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
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    # Preferred Gemini model (can be overridden in .env)
    GEMINI_MODEL: str = "gemini-2.5-pro"
    SCRAPEGRAPH_ENDPOINT: str = "http://localhost:8001/api/scrape"
    # Strapi configuration (production/staging)
    STRAPI_URL: str = ""
    STRAPI_TOKEN: str = ""

    # FootyStats API
    FOOTYSTATS_API_KEY: str = "f37d0d7b03a98882d9a3672336c2a30d89ade024875637d35b5cd5f224149d0e"
    FOOTYSTATS_BASE_URL: str = "https://api.football-data-api.com"
    # Optional JSON mapping of preset leagues, e.g. {"peru_liga1": {"league_id": 3439, "season": 2024}}
    FOOTYSTATS_PRESET_LEAGUES: str = ""
    
    # WordPress
    WP_GRAPHQL_ENDPOINT: str = "https://example.com/graphql"
    WP_AUTH_TOKEN: str = ""
    
    # Scraping
    SCRAPE_URLS: str = "https://rpp.pe/deportes,https://depor.com/,https://www.espn.com.pe/"

    # EasyPromos (autologin + promo link)
    EASYPROMOS_API_AUTLOGIN: str = "https://api.easypromosapp.com/v2/users/autologin/{campaign_id}"
    EASYPROMOS_PROMO_BASE: str = "https://a.cstmapp.com/p/{campaign_id}"
    # Optional defaults
    EASYPROMOS_API_TOKEN: str = ""
    EASYPROMOS_CAMPAIGN_ID: str = ""
    
    # CORS
    CORS_ORIGINS: str = "*"
    
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
    def footystats_presets(self) -> dict:
        """Return preset leagues mapping as dict"""
        import json

        raw = (self.FOOTYSTATS_PRESET_LEAGUES or "").strip()
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except Exception:
            return {}
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Singleton instance
settings = Settings()
