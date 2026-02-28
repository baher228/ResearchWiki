import os

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY")
    MISTRAL_MODEL: str = "mistral-medium-latest"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
