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
    
    # External Services
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    SCRAPEGRAPH_ENDPOINT: str = "http://localhost:8001/api/scrape"
    
    # WordPress
    WP_GRAPHQL_ENDPOINT: str = "https://example.com/graphql"
    WP_AUTH_TOKEN: str = ""
    
    # Scraping
    SCRAPE_URLS: str = "https://rpp.pe/deportes,https://depor.com/,https://www.espn.com.pe/"
    
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
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Singleton instance
settings = Settings()
