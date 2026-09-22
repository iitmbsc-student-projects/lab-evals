"""
Configuration loader for environment variables and settings.
Uses python-dotenv and lru_cache for efficient, environment-agnostic config.
"""

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Centralized application settings object."""

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-key")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    # Short-lived access token; the frontend silently refreshes it.
    JWT_EXPIRES_MINUTES: int = int(os.getenv("JWT_EXPIRES_MINUTES", "30"))
    # Long-lived refresh token; only its expiry forces a re-login.
    REFRESH_TOKEN_EXPIRES_DAYS: int = int(
        os.getenv("REFRESH_TOKEN_EXPIRES_DAYS", "7")
    )
    GOOGLE_CLIENT_ID: str = os.getenv(
        "GOOGLE_CLIENT_ID", "your-google-client-id"
    )
    ENV: str = os.getenv("ENV", "development")
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "sayan@study.iitm.ac.in")
    ADMIN_NAME: str = os.getenv("ADMIN_NAME", "Sayan")
    FRONTEND_ORIGIN: str = os.getenv(
        "FRONTEND_ORIGIN", "http://localhost:5173"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
