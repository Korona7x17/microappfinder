from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    # App
    APP_NAME: str = "MicroAppFinder"
    DEBUG: bool = False
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/microappfinder"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Qdrant (optional)
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str | None = None
    
    # LLM Providers
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    
    # Provider APIs
    REDDIT_CLIENT_ID: str | None = None
    REDDIT_CLIENT_SECRET: str | None = None
    REDDIT_USER_AGENT: str = "MicroAppFinder/0.1"
    
    PRODUCTHUNT_API_KEY: str | None = None
    
    # Scraping
    CRAWL4AI_TIMEOUT: int = 20
    FETCH_RATE_LIMIT: float = 1.0  # requests per second
    CACHE_TTL_HOURS: int = 48
    
    # LLM
    LLM_CHEAP_MODEL: str = "gpt-4o-mini"
    LLM_PREMIUM_MODEL: str = "gpt-4o"
    LLM_MAX_TOKENS: int = 2000
    
    # Scoring
    SCORE_PAIN_WEIGHT: float = 0.30
    SCORE_FREQUENCY_WEIGHT: float = 0.20
    SCORE_WTP_WEIGHT: float = 0.20
    SCORE_PULL_WEIGHT: float = 0.15
    SCORE_SOCIAL_WEIGHT: float = 0.10
    SCORE_URGENCY_WEIGHT: float = 0.05
    
    # Clustering
    MIN_SIGNALS_PER_CLUSTER: int = 5
    MAX_CLUSTERS: int = 20
    
    # Exports
    S3_BUCKET: str | None = None
    S3_REGION: str = "us-east-1"
    S3_ACCESS_KEY: str | None = None
    S3_SECRET_KEY: str | None = None
    
    # Monitoring
    SENTRY_DSN: str | None = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
