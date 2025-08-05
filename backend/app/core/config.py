from pydantic_settings import BaseSettings 
class Settings(BaseSettings):
    # ... your existing settings ...
    
    # Celery Configuration
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Redis Configuration (for caching later)
    REDIS_URL: str = "redis://localhost:6379/1"  # Different DB for caching
    
    class Config:
        env_file = ".env"

settings = Settings()