from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Worker settings"""
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/microappfinder"
    
    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str | None = None
    
    # LLM
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    
    # Provider APIs
    REDDIT_CLIENT_ID: str | None = None
    REDDIT_CLIENT_SECRET: str | None = None
    REDDIT_USER_AGENT: str | None = None
    PRODUCTHUNT_API_KEY: str | None = None

    # Environment
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"


settings = Settings()
