import os

from pydantic_settings import BaseSettings
from functools import lru_cache



class Settings(BaseSettings):
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")  # kept for reference
    MISTRAL_MODEL: str = os.getenv("MISTRAL_MODEL", "mistral.mistral-large-2402-v1:0")
    MISTRAL_FAST_MODEL: str = os.getenv("MISTRAL_FAST_MODEL", "mistral.mistral-large-2402-v1:0")

    # PostgreSQL (RDS)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # AWS S3
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_SESSION_TOKEN: str = os.getenv("AWS_SESSION_TOKEN", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "")

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
