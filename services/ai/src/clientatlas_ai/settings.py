from functools import lru_cache
from pathlib import Path
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
    object_storage_root: Path = Path(".clientatlas/storage")
    max_upload_bytes: int = 25 * 1024 * 1024
    ollama_base_url: AnyHttpUrl = AnyHttpUrl("http://127.0.0.1:11434")
    ollama_embedding_model: str = "nomic-embed-text"
    ollama_generation_model: str = "qwen2.5:7b"
    embedding_dimensions: int = 768
    llm_timeout_seconds: float = 90.0


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
