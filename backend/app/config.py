from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    MISTRAL_API_KEY: str = ""
    MISTRAL_MODEL: str = "mistral-large-latest"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
