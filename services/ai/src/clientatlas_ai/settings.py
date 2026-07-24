from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="CLIENTATLAS_",
        extra="ignore",
        frozen=True,
    )

    environment: Literal["development", "test", "production"] = "development"
    user_database_url: PostgresDsn
    supabase_jwt_issuer: AnyHttpUrl
    supabase_jwt_audience: str = "authenticated"
    supabase_jwks_url: AnyHttpUrl


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
