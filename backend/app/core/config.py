from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "CI Management API"
    VERSION: str = "3.0.0"
    DATABASE_URL: str = "sqlite:///./ci.db"
    SECRET_KEY: str = "change-me-in-production"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()