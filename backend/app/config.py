from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Scribbly"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "local"

    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    DATABASE_URL: str = "postgresql+asyncpg://artuser:artpass@localhost:5432/scribbly"
    REDIS_URL: str = "redis://localhost:6379/0"

    S3_BUCKET: str = "scribbly-dev"
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_KEY: str = "minioadmin"
    S3_SECRET: str = "minioadmin"
    S3_REGION: str = "us-east-1"

    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    MODEL_PATH: str = "./ai-engine/models"
    GPU_ENABLED: bool = False
    INFERENCE_TIMEOUT: int = 120

    RATE_LIMIT_FREE_TIER: int = 10
    RATE_LIMIT_WINDOW_SECONDS: int = 86400

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
